#!/bin/sh

SCRIPT_PATH="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)"
OS_NAME="$(uname -s)"
OS_ARCH="$(uname -p)"
install="install"
build="build"
LOG_BASE_DIR="${HOME}/logs"
LOG_DIR="${LOG_BASE_DIR}/logs_$(date +%Y%m%d_%H%M%S)"
WORK_DIR="/tmp/work_dir"
use_existing_log_dir="false"
build_rippled_opt="false"
build_witness_opt="false"
install_prerequisites_opt="false"
repo=""

trap cleanup EXIT


usage() {
  echo ""
  echo "Usage: $0 [Optional parameters]"
  echo "  --repo <path to repo if not under $HOME)>"

  exit 1
}

cleanup() {
  if [ -d "${WORK_DIR}" ]; then
    /bin/rm -rf "${WORK_DIR}"
  fi
}

prepare_workspace() {
  if [ "$(id -u)" -ne "0" ] ; then
    echo "This script must be executed with root privileges"
    exit 1
  fi

  if [ "${OS_NAME}" != "Linux" ]; then
    echo "Unsupported distro!"
    exit 1
  fi

  if [ -z "${repo}" ]; then
    if [ "${build_rippled_opt}" = "true" ]; then
      repo="${HOME}/rippled"
    elif [ "${build_witness_opt}" = "true" ]; then
      repo="${HOME}/xbridge_witness"
    fi
  fi

  if [ ! -d "${repo}" ]; then
    echo "Repo '${repo}' not found. Check help"
    exit 1
  fi

  mkdir -p "${WORK_DIR}"
  if [ "${use_existing_log_dir}" != "true" ]; then
    echo "Log directory: ${LOG_DIR}"
    mkdir -p "${LOG_DIR}"
  fi

  . "${SCRIPT_PATH}/setup_helper.sh"
}



while [ "$1" != "" ]; do
  case $1 in
  --repo)
    shift
    repo="$1"
    ;;

  --buildRippled)
    build_rippled_opt="true"
    ;;

  --buildWitness)
    build_witness_opt="true"
    ;;

  --logDir)
    shift
    use_existing_log_dir="true"
    LOG_DIR="${LOG_BASE_DIR}/$(basename "$1")"
    ;;

  --installPrerequisites)
    install_prerequisites_opt="true"
    ;;

  --help | *)
    usage
    ;;
  esac
  shift
done

prepare_workspace
install_prerequisites "${install_prerequisites_opt}"
build_rippled "${build_rippled_opt}" "${repo}"
build_witness "${build_witness_opt}" "${repo}"
