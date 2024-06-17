#!/bin/sh

SCRIPT_PATH="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)"
CLAUDIA_TMP_DIR="${HOME}/.claudia"
install="install"
build="build"
build_rippled_opt="false"
install_rippled_opt="false"
get_rippled_version_opt="false"
run_unittests_opt="false"
stop_network_opt="false"
start_network_opt="false"
validate_network_opt="false"
launch_explorer_opt="false"
switch_install_mode_opt="false"
enable_feature_opt="false"
clean_opt="false"
disable_feature_opt="false"
filtered_unittests_to_run=""
LOG_BASE_DIR="${HOME}/logs"
LOG_DIR="${LOG_BASE_DIR}/logs_$(date +%Y%m%d_%H%M%S)"
SCRIPT_HELPER="${SCRIPT_PATH}/lib/setup_helper.sh"
WORK_DIR="/tmp/work_dir"
ALT_HOST_SCRIPT_DIR="/tmp/network_setup"
network="rippled"  # TODO: Change this to mainnet?
default_network_rpc_endpoint="localhost:5001"
default_network_ws_endpoint="localhost:6001"
rippled_branch="master"


trap cleanup EXIT

usage() {
  echo ""
  echo "Usage: $0 [Optional parameters]"
  echo "  --rippledInstall (Install rippled)"
  echo "  --rippledBranch (Branch used to generate rippled binaries. Default: ${rippled_branch})"
  echo "  --rippledBuild (Build rippled)"
  echo "  --rippledVersion (Get rippled version)"
  echo "  --runUnittests (Run rippled unittests)"
  echo "  --repo <Path to rippled repo>"
  echo "  --enableFeature <feature (e.g. XChainBridge) to be enabled>"
  echo "  --disableFeature <feature (e.g. XChainBridge) to be disabled>"
  echo "  --networkStart (Start local rippled network)"
  echo "  --networkStop (Stop local rippled network)"
  echo "  --networkStatus (Get local rippled network status)"
  echo "  --setInstallMode <${install}/${build}>"
  echo "  --clean (Wipe out all traces of Claudia)"

  exit 1
}

cleanup() {
  /bin/rm -rf "${WORK_DIR}"
}

prepare_workspace() {
  unset DOCKER_DEFAULT_PLATFORM

  mkdir -p "${CLAUDIA_TMP_DIR}"
  if [ "${build_rippled_opt}" = "true" ]; then
    if [ ! -d "${repo}" ]; then
      echo "Unable to find repo. Check help"
      exit 1
    fi
  fi

  if [ "${build_rippled_opt}" = "true" ] || [ "${switch_install_mode_opt}" = "true" ] || [ "${install_rippled_opt}" = "true" ]; then
    echo "Log directory: ${LOG_DIR}"
    mkdir -p "${LOG_DIR}" "${WORK_DIR}"
  fi


  if [ "${network}" = "rippled" ]; then
    network_rpc_endpoint="${default_network_rpc_endpoint}"
    network_ws_endpoint="${default_network_ws_endpoint}"

    rippled_db_dirs="$HOME/rippled_db/rippled_1 $HOME/rippled_db/rippled_2"
    rippled_log_dirs="$HOME/rippled_log/rippled_1 $HOME/rippled_log/rippled_2"
  fi

  if [ "${start_network_opt}" = "true" ]; then
    echo "- Delete ${network} db & logs"
    for rippled_dir in ${rippled_db_dirs} ${rippled_log_dirs}; do
      /bin/rm -rf "${rippled_dir}"
      mkdir -p "${rippled_dir}"
      if [ ! -d "${rippled_dir}" ]; then
        parent_dir=$(dirname "${rippled_dir}")
        echo "Create '${parent_dir}' with write access"
        exit 1
      fi
    done
  fi

  . "${SCRIPT_HELPER}"
  docker network create "${DOCKER_NETWORK}" > /dev/null 2>&1

  host_script_dir="${SCRIPT_PATH}"
  is_script_in_home=$(echo "${PWD}" | grep "^${HOME}")
  if [ -z "${is_script_in_home}" ]; then
    if [ ! -d "${ALT_HOST_SCRIPT_DIR}" ]; then
      latest_scripts_not_found=true
    else
      latest_scripts_not_found=$(diff -rq "${host_script_dir}" "${ALT_HOST_SCRIPT_DIR}" | grep -v "${CONFIGS_DIR_NAME}")
    fi
    if [ -n "${latest_scripts_not_found}" ]; then
      /bin/cp -r "${host_script_dir}" "$(dirname "${ALT_HOST_SCRIPT_DIR}")"
    fi
    host_script_dir="${ALT_HOST_SCRIPT_DIR}"
  fi
}


if [ "$1" = "" ]; then
  usage
fi

while [ "$1" != "" ]; do
  case $1 in
  --repo)
    shift
    repo="$1"
    ;;

  --rippledBranch)
    shift
    rippled_branch="$1"
    ;;

  --rippledBuild)
    build_rippled_opt="true"
    install_mode="${build}"
    ;;

  --rippledInstall)
    install_rippled_opt="true"
    install_mode="${install}"
    ;;

  --rippledVersion)
    get_rippled_version_opt="true"
    ;;

  --runUnittests)
    run_unittests_opt="true"
    next_param=$(echo "$2" | grep "^--")
    if [ -z "${next_param}" ]; then
      filtered_unittests_to_run="${2:-$filtered_unittests_to_run}"
      shift
    fi
    ;;

  --networkStart)
    start_network_opt="true"
    next_param=$(echo "$2" | grep "^--")
    if [ -n "${next_param}" ]; then
      network="$2"
    fi
    ;;

  --networkStop)
    stop_network_opt="true"
    next_param=$(echo "$2" | grep "^--")
    if [ -n "${next_param}" ]; then
      network="$2"
    fi
    ;;

  --networkStatus)
    validate_network_opt="true"
    next_param=$(echo "$2" | grep "^--")
    if [ -n "${next_param}" ]; then
      network="$2"
    fi
    ;;

  --setInstallMode)
    switch_install_mode_opt="true"
    shift
    install_mode_to_switch="$1"
    ;;

  --enableFeature)
    enable_feature_opt="true"
    shift
    feature_name="$1"
    ;;

  --clean)
    clean_opt="true"
    ;;

  --disableFeature)
    disable_feature_opt="true"
    shift
    feature_name="$1"
    ;;

  --help | *)
    usage
    ;;
  esac
  shift
done

prepare_workspace
stop_network "${stop_network_opt}" "${network}" "${host_script_dir}"
docker_build_rippled "${build_rippled_opt}" "${install_mode}" "${host_script_dir}"
docker_install_rippled "${install_rippled_opt}" "${install_mode}" "${rippled_branch}"
docker_rippled_version "${get_rippled_version_opt}"
docker_run_unittests "${run_unittests_opt}" "${filtered_unittests_to_run}"
start_network "${start_network_opt}" "${network}" "${host_script_dir}"
validate_network "${validate_network_opt}" "${network_rpc_endpoint}"
launch_explorer "${launch_explorer_opt}" "${network_ws_endpoint}"
switch_install_mode "${switch_install_mode_opt}" "${install_mode_to_switch}"
enable_feature "${enable_feature_opt}" "${feature_name}"
disable_feature "${disable_feature_opt}" "${feature_name}"
clean "${clean_opt}"
