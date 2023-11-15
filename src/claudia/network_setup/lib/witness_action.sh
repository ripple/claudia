#!/bin/sh

SCRIPT_PATH="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)"
OS_NAME="$(uname -s)"
repo="${HOME}/xbridge_witness"
witness_exec="${repo}/linux_build/xbridge_witnessd"
witness_configs_dir="/opt/xbridge_witness/etc"
WORK_DIR="/tmp/work_dir"
witness_start_opt="false"
witness_stop_opt="false"
witness_status_opt="false"


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

exit_on_error() {
  exit_code=$1
  is_silent=$2
  if [ "${exit_code}" -ne 0 ]; then
    if [ "${is_silent}" != "${SILENT}" ]; then
      echo "Exit code: $exit_code"
    fi
    exit "${exit_code}"
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
}

delete_witness_db_and_logs() {
  echo "- Delete witness db & logs"
  for witness_config_file in "${witness_configs_dir}"/*json
  do
    witness_db_dir=$(grep DBDir "${witness_config_file}" | cut -d: -f2 | cut -d, -f1 | cut -d\" -f2 )
    if [ -d "${witness_db_dir}" ] && [ "${witness_db_dir}" != "." ]; then
      rm -rf "${witness_db_dir}"
      mkdir -p "${witness_db_dir}"
    fi
    witness_log_file=$(grep LogFile "${witness_config_file}" | cut -d: -f2 | cut -d, -f1 | cut -d\" -f2 )
    witness_log_dir=$(dirname "${witness_log_file}")
    if [ -d "${witness_log_dir}" ] && [ "${witness_log_dir}" != "." ]; then
      rm -rf "${witness_log_dir}"
      mkdir -p "${witness_log_dir}"
    fi
  done
}

witness_start() {
  l_witness_start_opt="$1"

  if [ "${l_witness_start_opt}" = "true" ]; then
    witness_stop true false
    delete_witness_db_and_logs

    echo "- Start witness servers"
    for witness_config_file in "${witness_configs_dir}"/*json
    do
      witness_db_dir=$(grep DBDir "${witness_config_file}" | cut -d: -f2 | cut -d, -f1 | cut -d\" -f2 )
      witness_log_file=$(grep LogFile "${witness_config_file}" | cut -d: -f2 | cut -d, -f1 | cut -d\" -f2 )
      mkdir -p "${witness_db_dir}" "$(dirname "${witness_log_file}")"

      "${witness_exec}" --conf "${witness_config_file}" --silent --verbose &
      pid=$! ;  sleep 1  # wait a second to get the process ID before the next instance starts
      process_running=$(ps | grep $pid | grep -v grep)
      if [ -z "${process_running}" ] ; then
        echo "** Error running witness server"
        tail -5 "${witness_log_file}"
        exit 1
      fi
      sleep 5
    done
  fi
}

witness_stop(){
  l_witness_stop_opt="$1"
  verbose="${2:-true}"

  if [ "${l_witness_stop_opt}" = "true" ]; then
    if [ "${verbose}" = "true" ]; then
      echo "- Stop witness servers"
    fi

    for witness_config_file in "${witness_configs_dir}"/*json
    do
      "${witness_exec}" --conf "${witness_config_file}" stop --silent > /dev/null 2>&1
    done
  fi
}

witness_status() {
  l_witness_status_opt="$1"
  if [ "${l_witness_status_opt}" = "true" ]; then
    for witness_config_file in "${witness_configs_dir}"/*json
    do
      "${witness_exec}" --conf "${witness_config_file}" server_info --silent > /dev/null 2>&1
      if [ "$?" = "0" ]; then
        echo "  Witness ${witness_config_file} running"
      else
        echo "  Witness ${witness_config_file} not running"
      fi
    done
  fi
}


while [ "$1" != "" ]; do
  case $1 in
  --witnessd)
    shift
    witness_exec="${1:-$witness_exec}"
    ;;

  --witnessConfigsPath)
    shift
    witness_configs_dir="${1:-$witness_configs_dir}"
    ;;

  --witnessStart)
    witness_start_opt="true"
    ;;

  --witnessStop)
    witness_stop_opt="true"
    ;;

  --witnessStatus)
    witness_status_opt="true"
    ;;

  --help | *)
    usage
    ;;
  esac
  shift
done

prepare_workspace
witness_start "${witness_start_opt}"
witness_stop "${witness_stop_opt}"
witness_status "${witness_status_opt}"
