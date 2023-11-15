#!/bin/sh

OS_NAME="$(uname -s)"
OS_ARCH="$(uname -p)"
PYTHON_VERSION=3.9
cmake_version=3.25.1
gcc_version=11
abi_version=11
cppstd=20

REMOUNT_VOLUME="false"
SILENT="silent"
DOCKER_RIPPLED_IMAGE="ksaxena0405/rippled-base:latest"
DOCKER_WITNESS_IMAGE="ksaxena0405/witness-server-base:latest"
DOCKER_NETWORK="rippled"
RIPPLED_NODE_CONTAINER_NAME=rippled_node
WITNESS_SERVER_CONTAINER_NAME=witness_node
RIPPLED_BUILD_CONTAINER_NAME=rippled_build
WITNESS_BUILD_CONTAINER_NAME=witness_build
MAC_CHROME_BROWSER="/Applications/Google Chrome.app"
LINUX_CHROME_BROWSER="chrome"
EXPLORER_URL_PREFIX="https://custom.xrpl.org"
BUILD_DIR_NAME="linux_build"
CONFIGS_DIR_NAME="configs"
INSTALL_MODE_FILE="${CLAUDIA_TMP_DIR}/install_mode"
RIPPLED_BIN_PATH="/opt/ripple/bin"
RIPPLED_BUILD_CONTAINER_CONFIG_PATH="/opt/xbridge_witness/etc"
RIPPLED_REPO_VALIDITY_CHECK_FILE="src/ripple/protocol/Feature.h"
WITNESS_REPO_VALIDITY_CHECK_FILE="src/xbwd/rpc/RPCCall.h"
RIPPLED_REPO_BUILT="${CLAUDIA_TMP_DIR}/rippled_repo_built"
WITNESS_REPO_BUILT="${CLAUDIA_TMP_DIR}/witness_repo_built"
RIPPLED_CONFIG_FEATURES_STANZA_NAME="\[features\]"
CONTAINER_HOME="/root"
RIPPLED_BUILD_CONTAINER_SCRIPT_DIR="${CONTAINER_HOME}/network_setup"
RIPPLED_BUILD_CONTAINER_LOG_DIR="${CONTAINER_HOME}/logs"
RIPPLED_BUILD_CONTAINER_HOST_RIPPLED_EXEC_LOC="${CONTAINER_HOME}/host_rippled_exec"
RIPPLED_BUILD_CONTAINER_HOST_WITNESS_EXEC_LOC="${CONTAINER_HOME}/host_witness_exec"
RIPPLED_BUILD_CONTAINER_BUILD_SCRIPT="${RIPPLED_BUILD_CONTAINER_SCRIPT_DIR}/lib/build.sh"
RIPPLED_BUILD_CONTAINER_WITNESS_ACTION_SCRIPT="${RIPPLED_BUILD_CONTAINER_SCRIPT_DIR}/lib/witness_action.sh"
RIPPLED_BUILD_CONTAINER_RIPPLED_HOME="${CONTAINER_HOME}/rippled"
RIPPLED_BUILD_CONTAINER_WITNESS_HOME="${CONTAINER_HOME}/xbridge_witness"
RIPPLED_CONFIGS_DIR="${CONFIGS_DIR_NAME}/rippled"
WITNESS_CONFIGS_DIR="${CONFIGS_DIR_NAME}/sidechain/witness"
RIPPLED_CONFIGS_FILE="${RIPPLED_CONFIGS_DIR}/rippled_*/rippled.cfg"
RIPPLED_BUILD_CONTAINER_BUILT_RIPPLED_EXEC="${RIPPLED_BUILD_CONTAINER_RIPPLED_HOME}/${BUILD_DIR_NAME}/rippled"
RIPPLED_BUILD_CONTAINER_INSTALLED_RIPPLED_EXEC="${RIPPLED_BIN_PATH}/rippled"
RIPPLED_NODE_DOCKER_FILE_DIR="${SCRIPT_PATH}"
RIPPLED_NODE_DOCKER_FILE_BUILD_MODE="${RIPPLED_NODE_DOCKER_FILE_DIR}/Dockerfile.rippled_build"
RIPPLED_NODE_DOCKER_FILE_INSTALL_MODE="${RIPPLED_NODE_DOCKER_FILE_DIR}/Dockerfile.rippled_install"
NETWORK_VALIDATION_SCRIPT="${SCRIPT_PATH}/lib/validate_network.py"
XCHAIN_BRIDGE_CREATE_SCRIPT="${SCRIPT_PATH}/lib/xchain_bridge_create.py"
DOCKER_NETWORK_CONFIG="${SCRIPT_PATH}/lib/rippled_network.yml"
DOCKER_XCHAIN_NETWORK_CONFIG="${SCRIPT_PATH}/lib/sidechain_network.yml"
RIPPLED_EXEC_RELATIVE_BUILD_PATH="${BUILD_DIR_NAME}/rippled"
WITNESS_EXEC_RELATIVE_BUILD_PATH="${BUILD_DIR_NAME}/xbridge_witnessd"
package_versions_log="${LOG_DIR}/package_versions.log"

detect_update_install_mode() {
  l_install_mode_to_switch="$1"

  if [ -n "${l_install_mode_to_switch}" ]; then
    echo "${l_install_mode_to_switch}" > "${INSTALL_MODE_FILE}"
  fi
  MODE=$(cat ${INSTALL_MODE_FILE} 2> /dev/null)
}
detect_update_install_mode

exit_on_error() {
  exit_code=$1
  is_silent=$2

  if [ "${exit_code}" -ne 0 ]; then
    if [ "${is_silent}" != "${SILENT}" ]; then
      echo "Exit code: $exit_code (check logs if available)"
    fi
    exit "${exit_code}"
  fi
}

set_arch_config() {
  if [ "${OS_ARCH}" = "arm" ]; then
    export DOCKER_DEFAULT_PLATFORM=linux/amd64
  fi
}

reset_timer() {
  start_time=$(date +%s)
}

print_elapsed_time() {
    end_time=$(date +%s)
    time_elapsed=$((end_time-start_time))
    echo "  Time elapsed: $((${time_elapsed} / 3600)) hr $(((${time_elapsed} / 60) % 60)) min $((${time_elapsed} % 60)) sec"
}

is_rippled_built_or_installed() {
  if [ ! -f "${INSTALL_MODE_FILE}" ]; then
    echo "Seems like rippled has not been built/installed. Please build or install rippled first"
    exit 1
  fi
}

is_rippled_built() {
  rippled_exec_loc_saved_in_container=$(docker exec ${RIPPLED_BUILD_CONTAINER_NAME} cat "${RIPPLED_BUILD_CONTAINER_HOST_RIPPLED_EXEC_LOC}" 2> /dev/null)
  if [ ! -f "${rippled_exec_loc_saved_in_container}" ]; then
    echo "rippled not built successfully. Rebuild rippled if required"
    exit 1
  fi
}

is_witness_built() {
  witness_exec_loc_saved_in_container=$(docker exec ${WITNESS_BUILD_CONTAINER_NAME} cat "${RIPPLED_BUILD_CONTAINER_HOST_WITNESS_EXEC_LOC}" 2> /dev/null)
  if [ ! -f "${witness_exec_loc_saved_in_container}" ]; then
    echo "xbridge_witness binary not found. Rebuild xbridge_witnessd if required"
    exit 1
  fi
}

set_network_config() {
  network="$1"

  if [ "${network}" = "rippled" ]; then
    network_config="${DOCKER_NETWORK_CONFIG}"
  fi
  if [ "${network}" = "sidechain" ]; then
    network_config="${DOCKER_XCHAIN_NETWORK_CONFIG}"
  fi
}

set_rippled_node_env() {
  rippled_build_path="$1"

  RIPPLED_BUILD_DIR=/dev/null
  RIPPLED_BIN_DIR=/dev/null
  RIPPLED_CONFIG_DIR="${host_script_dir}/${RIPPLED_CONFIGS_DIR}"
  DOCKER_NETWORK="${DOCKER_NETWORK}"
  if [ "${MODE}" = "${build}" ] && [ -d "${rippled_build_path}" ]; then
    RIPPLED_BUILD_DIR="${rippled_build_path}"
    RIPPLED_BIN_DIR="${RIPPLED_BIN_PATH}"
  fi
  export RIPPLED_BUILD_DIR=${RIPPLED_BUILD_DIR}
  export RIPPLED_BIN_DIR=${RIPPLED_BIN_DIR}
  export RIPPLED_CONFIG_DIR="${host_script_dir}/${RIPPLED_CONFIGS_DIR}"
  export DOCKER_NETWORK="${DOCKER_NETWORK}"
}

install_os_packages() {
  echo "- Install OS packages"
  time_now="$(date +%Y%m%d_%H%M%S)"
  log_file="${LOG_DIR}/${time_now}_prerequisite.log"

  apt -y update >>"${log_file}" 2>&1 && \
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tzdata >>"${log_file}" 2>&1 && \
  apt -y install sysstat dnsutils net-tools vim apt-transport-https ca-certificates >>"${log_file}" 2>&1 && \
  apt -y install wget gnupg apt-utils docker docker-compose >>"${log_file}" 2>&1 && \
  apt -y install software-properties-common >>"${log_file}" 2>&1 && \
  add-apt-repository -y ppa:deadsnakes/ppa >>"${log_file}" 2>&1 && \
  apt update >>"${log_file}" 2>&1 && \
  apt -y install python${PYTHON_VERSION} python3-pip >>"${log_file}" 2>&1
  exit_on_error $?
  update-alternatives --install /usr/local/bin/python3 python3 /usr/bin/python${PYTHON_VERSION} 3 > /dev/null 2>&1
  exit_on_error $?

  python3 --version >> "${package_versions_log}" 2>&1
  exit_on_error $?
}

update_gcc() {
  echo "- Update gcc"
  time_now="$(date +%Y%m%d_%H%M%S)"
  log_file="${LOG_DIR}/${time_now}_gcc.log"

  apt-get -y update >> "${log_file}" 2>&1 && \
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tzdata >>"${log_file}" 2>&1 && \
  apt-get -y dist-upgrade >> "${log_file}" 2>&1 && \
  apt-get -y install build-essential software-properties-common >> "${log_file}" 2>&1 && \
  add-apt-repository -y ppa:ubuntu-toolchain-r/test >> "${log_file}" 2>&1 && \
  apt-get -y update >> "${log_file}" 2>&1

  update-alternatives --force --remove-all gcc >> "${log_file}" 2>&1
  apt-get -o Dpkg::Options::="--force-confnew" -y install gcc-${gcc_version} g++-${gcc_version} >> "${log_file}" 2>&1 && \
  update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-${gcc_version} 60 --slave /usr/bin/g++ g++ /usr/bin/g++-${gcc_version} >> "${log_file}" 2>&1 && \
  update-alternatives --config gcc >> "${log_file}" 2>&1
  exit_on_error $?

  gcc --version >> "${package_versions_log}" 2>&1
  exit_on_error $?
}

install_cmake() {
  echo "- Install cmake"
  time_now="$(date +%Y%m%d_%H%M%S)"
  log_file="${LOG_DIR}/${time_now}_cmake_install.log"

  cmake_script="cmake-${cmake_version}-Linux-${OS_ARCH}.sh"
  wget -q -P "${WORK_DIR}" https://github.com/Kitware/CMake/releases/download/v"${cmake_version}"/"${cmake_script}"
  exit_on_error $?
  sh "${WORK_DIR}/${cmake_script}" --prefix=/usr/local --exclude-subdir >> "${log_file}" 2>&1

  cmake --version >> "${package_versions_log}" 2>&1
  exit_on_error $?
}

install_conan() {
  echo "- Install conan"
  time_now="$(date +%Y%m%d_%H%M%S)"
  log_file="${LOG_DIR}/${time_now}_conan_setup.log"

  pip install --upgrade 'conan<2' > "${log_file}" 2>&1
  conan profile new default --detect >> "${log_file}" 2>&1
  conan profile update settings.compiler.cppstd=${cppstd} default >> "${log_file}" 2>&1
  conan profile update settings.compiler.libcxx=libstdc++${abi_version} default >> "${log_file}" 2>&1
  conan profile show default >> "${package_versions_log}" 2>&1
  exit_on_error $?

  conan --version >> "${package_versions_log}" 2>&1
  exit_on_error $?
}

install_prerequisites() {
  install_prerequisites_opt="$1"

  if [ "${install_prerequisites_opt}" = "true" ]; then
    install_os_packages
    update_gcc
    install_cmake
    install_conan
  fi
}

build_rippled() {
  l_build_rippled_opt="$1"
  repo="$2"

  if [ "${l_build_rippled_opt}" = "true" ]; then
    reset_timer
    echo "- Build rippled"

    CWD=$(pwd)
    cd "${repo}" || exit
    build_path="${repo}/${BUILD_DIR_NAME}"
    time_now="$(date +%Y%m%d_%H%M%S)"
    conan export external/snappy snappy/1.1.10@ > "${LOG_DIR}/${time_now}_rippled_snappy.log" 2>&1
    conan export external/soci soci/4.0.3@ > "${LOG_DIR}/${time_now}_rippled_soci.log" 2>&1
    exit_on_error $? "${SILENT}"

    mkdir -p "${build_path}" ; cd "${build_path}" || exit
    echo "  . conan install"
    time_now="$(date +%Y%m%d_%H%M%S)"
    conan install .. --output-folder . --build missing --settings build_type=Release > "${LOG_DIR}/${time_now}_rippled_conan_install.log" 2>&1
    exit_on_error $? "${SILENT}"

    time_now="$(date +%Y%m%d_%H%M%S)"
    cmake -DCMAKE_TOOLCHAIN_FILE:FILEPATH=build/generators/conan_toolchain.cmake -DCMAKE_BUILD_TYPE=Release .. > "${LOG_DIR}/${time_now}_rippled_cmake.log" 2>&1
    exit_on_error $? "${SILENT}"

    echo "  . cmake"
    time_now="$(date +%Y%m%d_%H%M%S)"
    cmake --build . -- -j $(nproc) > "${LOG_DIR}/${time_now}_rippled_cmake_build.log" 2>&1
    exit_on_error $? "${SILENT}"
    cd "${CWD}" || exit
    print_elapsed_time
  fi
}

build_witness() {
  l_build_witness_opt="$1"
  repo="$2"

  if [ "${l_build_witness_opt}" = "true" ]; then
    reset_timer
    echo "- Build witness"

    CWD=$(pwd)
    build_path="${repo}/${BUILD_DIR_NAME}"
    mkdir -p "${build_path}" ; cd "${build_path}" || exit
    echo "  . conan install"
    time_now="$(date +%Y%m%d_%H%M%S)"
    conan install .. --output-folder . --build missing --settings build_type=Release > "${LOG_DIR}/${time_now}_witness_conan_install.log" 2>&1
    exit_on_error $? "${SILENT}"

    time_now="$(date +%Y%m%d_%H%M%S)"
    if [ -f "${RIPPLED_BUILD_CONTAINER_BUILT_RIPPLED_EXEC}" ]; then
      rippled_build_path=$(dirname "${RIPPLED_BUILD_CONTAINER_BUILT_RIPPLED_EXEC}")
      rippled_home=$(dirname "${rippled_build_path}")
      echo "  . Using prebuilt rippled home: ${rippled_home}"
      cmake -DCMAKE_TOOLCHAIN_FILE:FILEPATH=build/generators/conan_toolchain.cmake \
        -DRIPPLE_SRC_DIR="${rippled_home}" \
        -DRIPPLE_BIN_DIR="${rippled_build_path}" \
        -DCMAKE_BUILD_TYPE=Release .. > "${LOG_DIR}/${time_now}_witness_cmake.log" 2>&1
    else
      cmake -DCMAKE_TOOLCHAIN_FILE:FILEPATH=build/generators/conan_toolchain.cmake \
        -DCMAKE_BUILD_TYPE=Release .. > "${LOG_DIR}/${time_now}_witness_cmake.log" 2>&1
    fi
    exit_on_error $? "${SILENT}"

    echo "  . cmake"
    time_now="$(date +%Y%m%d_%H%M%S)"
    cmake --build . -- -j $(nproc) > "${LOG_DIR}/${time_now}_witness_cmake_build.log" 2>&1
    exit_on_error $? "${SILENT}"
    cd "${CWD}" || exit
    print_elapsed_time
  fi
}

remount_repo_volume() {
  repo_to_mount="$1"
  build_container="$2"
  repo_built="$3"

  if [ -f "${repo_built}" ]; then
    if [ "$(cat "${repo_built}")" != "${repo_to_mount}" ]; then
      echo "  Mounting repo '${repo_to_mount}'"
      docker rm -f "${build_container}" > /dev/null 2>&1
      REMOUNT_VOLUME="true"
    fi
  fi
  echo "${repo}" > "${repo_built}"
}

docker_build_rippled() {
  l_build_rippled_opt="$1"
  install_mode="$2"
  host_script_dir="$3"

  if [ "${l_build_rippled_opt}" = "true" ]; then
    if [ ! -f "${repo}/${RIPPLED_REPO_VALIDITY_CHECK_FILE}" ]; then
      echo "${repo} doesn't seem to be a valid rippled repository"
      exit 1
    fi
    echo "- Docker build rippled"
    remount_repo_volume "${repo}" "${RIPPLED_BUILD_CONTAINER_NAME}" "${RIPPLED_REPO_BUILT}"
    time_now="$(date +%Y%m%d_%H%M%S)"
    log_file="${LOG_DIR}/${time_now}_rippled_build.log"

    if [ ! "$(docker ps -aq --filter name=${RIPPLED_BUILD_CONTAINER_NAME})" ] || [ "${REMOUNT_VOLUME}" = "true" ]; then
      docker run \
      --net ${DOCKER_NETWORK} \
        --name "${RIPPLED_BUILD_CONTAINER_NAME}" -i -d \
        -v "${repo}":"${RIPPLED_BUILD_CONTAINER_RIPPLED_HOME}" \
        -v "${host_script_dir}":"${RIPPLED_BUILD_CONTAINER_SCRIPT_DIR}" \
        -v "${LOG_BASE_DIR}":"${RIPPLED_BUILD_CONTAINER_LOG_DIR}" \
        "${DOCKER_RIPPLED_IMAGE}" > "${log_file}" 2>&1
    elif [ "$(docker ps -aq --filter name=${RIPPLED_BUILD_CONTAINER_NAME} --filter status=exited)" ]; then
      docker start "${RIPPLED_BUILD_CONTAINER_NAME}" > "${log_file}" 2>&1
    fi

    docker exec ${RIPPLED_BUILD_CONTAINER_NAME} \
      sh -c "rm -f ${RIPPLED_BUILD_CONTAINER_HOST_RIPPLED_EXEC_LOC}"
    docker exec ${RIPPLED_BUILD_CONTAINER_NAME} \
      sh "${RIPPLED_BUILD_CONTAINER_BUILD_SCRIPT}" --buildRippled --logDir "${LOG_DIR}"
    exit_on_error $?

    rippled_exec="${repo}/${RIPPLED_EXEC_RELATIVE_BUILD_PATH}"
    docker exec "${RIPPLED_BUILD_CONTAINER_NAME}" \
      sh -c "echo ${rippled_exec} > ${RIPPLED_BUILD_CONTAINER_HOST_RIPPLED_EXEC_LOC}"
    detect_update_install_mode "${install_mode}"
  fi
}

docker_install_rippled() {
  l_install_rippled_opt="$1"
  install_mode="$2"
  rippled_branch="$3"

  if [ "${l_install_rippled_opt}" = "true" ]; then
      echo "- Docker install rippled"
      set_arch_config
      stop_all_networks "${SILENT}"
      time_now="$(date +%Y%m%d_%H%M%S)"
      log_file="${LOG_DIR}/${time_now}_rippled_install.log"
      docker build -t ${RIPPLED_NODE_CONTAINER_NAME} -f "${RIPPLED_NODE_DOCKER_FILE_INSTALL_MODE}" --build-arg RIPPLED_BRANCH="${rippled_branch}" . > "${log_file}" 2>&1
      exit_on_error $?
      detect_update_install_mode "${install_mode}"
  fi
}

docker_build_witness() {
  l_build_witness_opt="$1"
  install_mode="$2"
  host_script_dir="$3"

  if [ "${l_build_witness_opt}" = "true" ]; then
    if [ ! -f "${repo}/${WITNESS_REPO_VALIDITY_CHECK_FILE}" ]; then
      echo "${repo} doesn't seem to be a valid witness repository"
      exit 1
    fi

    echo "- Docker build witness"
    remount_repo_volume "${repo}" "${WITNESS_BUILD_CONTAINER_NAME}" "${WITNESS_REPO_BUILT}"
    if [ ! "$(docker ps -aq --filter name=${WITNESS_BUILD_CONTAINER_NAME})" ] || [ "${REMOUNT_VOLUME}" = "true" ]; then
      rippled_exec_loc_saved_in_container=$(docker exec "${RIPPLED_BUILD_CONTAINER_NAME}" cat "${RIPPLED_BUILD_CONTAINER_HOST_RIPPLED_EXEC_LOC}" 2> /dev/null)
      if [ -f "${rippled_exec_loc_saved_in_container}" ]; then
        rippled_build_path=$(dirname "${rippled_exec_loc_saved_in_container}")
        rippled_home=$(dirname "${rippled_build_path}")
        export RIPPLED_HOME_DIR="${rippled_home}"
      else
        export RIPPLED_HOME_DIR=/dev/null
      fi

      time_now="$(date +%Y%m%d_%H%M%S)"
      log_file="${LOG_DIR}/${time_now}_witness_build.log"

      docker run \
        --net ${DOCKER_NETWORK} \
        --name "${WITNESS_BUILD_CONTAINER_NAME}" -i -d \
        -v "${repo}":"${RIPPLED_BUILD_CONTAINER_WITNESS_HOME}" \
        -v "${host_script_dir}":"${RIPPLED_BUILD_CONTAINER_SCRIPT_DIR}" \
        -v "${LOG_BASE_DIR}":"${RIPPLED_BUILD_CONTAINER_LOG_DIR}" \
        "${DOCKER_WITNESS_IMAGE}" > "${log_file}" 2>&1
    elif [ "$(docker ps -aq --filter name=${WITNESS_BUILD_CONTAINER_NAME} --filter status=exited)" ]; then
      docker start "${WITNESS_BUILD_CONTAINER_NAME}"
    fi

    docker exec ${WITNESS_BUILD_CONTAINER_NAME} \
      sh -c "rm -f ${RIPPLED_BUILD_CONTAINER_HOST_WITNESS_EXEC_LOC}"
    docker exec ${WITNESS_BUILD_CONTAINER_NAME} \
      sh "${RIPPLED_BUILD_CONTAINER_BUILD_SCRIPT}" --buildWitness --logDir "${LOG_DIR}"
    exit_on_error $?

    witness_exec="${repo}/${WITNESS_EXEC_RELATIVE_BUILD_PATH}"
    docker exec ${WITNESS_BUILD_CONTAINER_NAME} \
      sh -c "echo ${witness_exec} > ${RIPPLED_BUILD_CONTAINER_HOST_WITNESS_EXEC_LOC}"
  fi
}

start_network() {
  l_start_network_opt="$1"
  network="$2"
  host_script_dir="$3"
  set_network_config "${network}"
  if [ "${l_start_network_opt}" = "true" ]; then
    reset_timer
    is_rippled_built_or_installed
    if [ "${MODE}" = "${build}" ]; then
      is_rippled_built
      rippled_build_path=$(dirname "${rippled_exec_loc_saved_in_container}")
      rippled_home=$(dirname "${rippled_build_path}")
      echo "- Start ${network} network (with built rippled)"
      echo "  rippled repo: ${rippled_home}"

      docker build --quiet -t ${RIPPLED_NODE_CONTAINER_NAME} -f "${RIPPLED_NODE_DOCKER_FILE_BUILD_MODE}" . > /dev/null 2>&1
    else
      disable_feature true XChainBridge  # TODO: Temporary workaround until sidechain is released/packaged
      echo "- Start ${network} network (with installed rippled)"
      rippled_build_path=""
    fi
    set_rippled_node_env "${rippled_build_path}"
    docker-compose -f "${network_config}" down > /dev/null 2>&1
    docker-compose -f "${network_config}" up -d > /dev/null 2>&1

    validate_network true "${network_rpc_endpoint}"
    launch_explorer true "${network_ws_endpoint}"
    print_elapsed_time
  fi
}

stop_network() {
  l_stop_network_opt="$1"
  network="$2"
  host_script_dir="$3"

  set_network_config "${network}"
  if [ "${l_stop_network_opt}" = "true" ]; then
    echo "- Stop network $network"

    if [ -f "${RIPPLED_REPO_BUILT}" ]; then
      rippled_build_path="$(cat "${RIPPLED_REPO_BUILT}")/${BUILD_DIR_NAME}"
    else
      rippled_build_path=""
    fi
    set_rippled_node_env "${rippled_build_path}"
    docker-compose -f "${network_config}" down > /dev/null 2>&1
  fi
}

validate_network() {
  l_validate_network_opt="$1"
  network_rpc_endpoint="$2"
  set_network_config "${network}"

  if [ "${l_validate_network_opt}" = "true" ]; then
    echo "- Validate ${network} network"
    python3 "${NETWORK_VALIDATION_SCRIPT}" --rippledServer "${network_rpc_endpoint}"
    status=$?
    if [ "${status}" -ne 0 ]; then
      rippled_node_ids=$(docker ps -aq --filter ancestor=${RIPPLED_NODE_CONTAINER_NAME} | tr '\n' ' ')
      for rippled_node_id in ${rippled_node_ids}
      do
        if [ -n "${rippled_node_ids}" ]; then
          echo ""
          echo "  ** rippled logs **"
          docker logs -n5 "${rippled_node_id}"
        fi
      done
      exit 1
    fi
  fi
}

launch_explorer() {
  l_launch_explorer_opt="$1"
  network_ws_endpoint="$2"

  if [ "${l_launch_explorer_opt}" = "true" ]; then
    if [ "${OS_NAME}" = "Linux" ]; then
      WEB_BROWSER="${LINUX_CHROME_BROWSER}"
    else
      WEB_BROWSER="${MAC_CHROME_BROWSER}"
    fi
    browser_name=$(echo "${WEB_BROWSER}" | awk '{ print $NF }')
    echo "- Launch Explorer (${browser_name}): ${EXPLORER_URL_PREFIX}/${network_ws_endpoint}"

    if [ -d "${WEB_BROWSER}" ] || [ -f "${WEB_BROWSER}" ]; then
      /usr/bin/open -a "${WEB_BROWSER}" "${EXPLORER_URL_PREFIX}/${network_ws_endpoint}"
    fi
  fi
}

stop_all_networks() {
  is_silent=$1

  if [ "${is_silent}" != "${SILENT}" ]; then
    echo "  Stop all rippled networks & witness servers"
  fi

  docker rm -f $(docker ps -aq --filter ancestor=${RIPPLED_NODE_CONTAINER_NAME}) > /dev/null 2>&1
  docker rm -f $(docker ps -aq --filter name=${WITNESS_SERVER_CONTAINER_NAME}) > /dev/null 2>&1
  if [ "${MODE}" = "${build}" ]; then
    docker rmi -f ${RIPPLED_NODE_CONTAINER_NAME} > /dev/null 2>&1
  fi
}

docker_run_unittests() {
  l_run_unittests_opt="$1"
  filtered_unittests_to_run="$2"

  if [ "${l_run_unittests_opt}" = "true" ]; then
    is_rippled_built_or_installed
    echo "- Run unittests"
    if [ "${MODE}" = "${build}" ]; then
      if [ ! "$(docker ps -aq --filter name=${RIPPLED_BUILD_CONTAINER_NAME})" ]; then
        docker run \
          --name "${RIPPLED_BUILD_CONTAINER_NAME}" -i -d \
          -v "${repo}":"${RIPPLED_BUILD_CONTAINER_RIPPLED_HOME}" \
          -v "${host_script_dir}":"${RIPPLED_BUILD_CONTAINER_SCRIPT_DIR}" \
          -v "${LOG_BASE_DIR}":"${RIPPLED_BUILD_CONTAINER_LOG_DIR}" \
          "${DOCKER_RIPPLED_IMAGE}" > /dev/null 2>&1
      elif [ "$(docker ps -aq --filter name=${RIPPLED_BUILD_CONTAINER_NAME} --filter status=exited)" ]; then
        docker start "${RIPPLED_BUILD_CONTAINER_NAME}"
      fi

      is_rippled_built
      docker exec "${RIPPLED_BUILD_CONTAINER_NAME}" "${RIPPLED_BUILD_CONTAINER_BUILT_RIPPLED_EXEC}" --unittest "${filtered_unittests_to_run}"
      exit_on_error $?
    else
      set_arch_config
      first_node_container=$(docker ps | grep "${RIPPLED_NODE_CONTAINER_NAME}" | awk '{ print $1 }' 2>&1 | head -n 1)
      if [ -z "$first_node_container" ]; then
        docker run --rm "${RIPPLED_NODE_CONTAINER_NAME}" "${RIPPLED_BUILD_CONTAINER_INSTALLED_RIPPLED_EXEC}" --unittest "${filtered_unittests_to_run}"
        exit_on_error $?
      else
        docker exec "${first_node_container}" "${RIPPLED_BUILD_CONTAINER_INSTALLED_RIPPLED_EXEC}" --unittest "${filtered_unittests_to_run}"
        exit_on_error $?
      fi
    fi
  fi
}

docker_rippled_version() {
  get_rippled_version_opt="$1"

  if [ "${get_rippled_version_opt}" = "true" ]; then
    is_rippled_built_or_installed
    if [ "${MODE}" = "${build}" ]; then
      is_rippled_built
      docker exec "${RIPPLED_BUILD_CONTAINER_NAME}" "${RIPPLED_BUILD_CONTAINER_BUILT_RIPPLED_EXEC}" --version
      exit_on_error $?
    else
      set_arch_config
      first_node_container=$(docker ps | grep "${RIPPLED_NODE_CONTAINER_NAME}" | awk '{ print $1 }' 2>&1 | head -n 1)
      if [ -z "$first_node_container" ]; then
        docker run --rm "${RIPPLED_NODE_CONTAINER_NAME}" "${RIPPLED_BUILD_CONTAINER_INSTALLED_RIPPLED_EXEC}" --version
        exit_on_error $?
      else
        docker exec "${first_node_container}" "${RIPPLED_BUILD_CONTAINER_INSTALLED_RIPPLED_EXEC}" --version
        exit_on_error $?
      fi
    fi
  fi
}

witness_action() {
  l_witness_action_opt="$1"
  witness_action="$2"
  host_script_dir="$3"

  if [ "${l_witness_action_opt}" = "true" ]; then
    witness="witness"
    action=$(echo "${witness_action}" | sed -e "s/--${witness}//g")
    echo "- Docker ${witness} ${action}"
    if [ -f "${WITNESS_REPO_BUILT}" ]; then
      witness_repo=$(cat "${WITNESS_REPO_BUILT}")
      if [ ! "$(docker ps -aq --filter name=${WITNESS_SERVER_CONTAINER_NAME})" ]; then
        WITNESS_CONFIGS_DIR_PATH="${host_script_dir}/${WITNESS_CONFIGS_DIR}"
        docker run \
          --net ${DOCKER_NETWORK} \
          --name "${WITNESS_SERVER_CONTAINER_NAME}" -i -d \
          -v "${witness_repo}":"${RIPPLED_BUILD_CONTAINER_WITNESS_HOME}" \
          -v "${host_script_dir}":"${RIPPLED_BUILD_CONTAINER_SCRIPT_DIR}" \
          -v "${LOG_BASE_DIR}":"${RIPPLED_BUILD_CONTAINER_LOG_DIR}" \
          -v "${WITNESS_CONFIGS_DIR_PATH}":"${RIPPLED_BUILD_CONTAINER_CONFIG_PATH}" \
          "${DOCKER_WITNESS_IMAGE}" > /dev/null 2>&1
      elif [ "$(docker ps -aq --filter name=${WITNESS_SERVER_CONTAINER_NAME} --filter status=exited)" ]; then
        docker start "${WITNESS_SERVER_CONTAINER_NAME}"
      fi

      is_witness_built
      docker exec ${WITNESS_SERVER_CONTAINER_NAME} \
        sh  "${RIPPLED_BUILD_CONTAINER_WITNESS_ACTION_SCRIPT}" "${witness_action}"
      exit_on_error $?

      if [ "${witness_action}" = "--witnessStop" ]; then
        docker rm -f ${WITNESS_SERVER_CONTAINER_NAME} > /dev/null 2>&1
      fi
    else
      echo "Error: witness not built. Check help"
      exit 1
    fi
  fi
}

start_sidechain() {
  l_start_sidechain_opt="$1"
  network="$2"
  host_script_dir="$3"
  witness_action="$4"

  if [ "${l_start_sidechain_opt}" = "true" ]; then
    if [ "${MODE}" = "${build}" ]; then
      is_rippled_built
      is_witness_built

      start_network true "${network}" "${host_script_dir}"
      WITNESS_CONFIGS_DIR_PATH="${host_script_dir}/${WITNESS_CONFIGS_DIR}"
      python3 "${XCHAIN_BRIDGE_CREATE_SCRIPT}" --witnessConfigDir "${WITNESS_CONFIGS_DIR_PATH}"
      witness_action true "${witness_action}" "${host_script_dir}"
      python3 "${XCHAIN_BRIDGE_CREATE_SCRIPT}" --xChainTransfer --witnessConfigDir "${WITNESS_CONFIGS_DIR_PATH}"
    else
      echo "Currently, Sidechain is not support in install mode"
      echo "Please switch to ${build} mode."
      exit 1
    fi
  fi
}

stop_sidechain() {
  l_stop_sidechain_opt="$1"
  network="$2"
  host_script_dir="$3"
  witness_action="$4"

  if [ "${l_stop_sidechain_opt}" = "true" ]; then
    witness_action true "${witness_action}" "${host_script_dir}"
    stop_network true "${network}" "${host_script_dir}"
  fi
}

switch_install_mode() {
  l_switch_install_mode_opt="$1"
  install_mode_to_switch="$2"

  if [ "${l_switch_install_mode_opt}" = "true" ]; then
    is_rippled_built_or_installed
    if [ "${install_mode_to_switch}" = "${build}" ] && [ -f "${RIPPLED_REPO_BUILT}" ]; then
      echo "- Switching install mode to build"
      detect_update_install_mode "${install_mode_to_switch}"
      stop_all_networks
    fi

    if [ "${install_mode_to_switch}" = "${install}" ]; then
      echo "- Switching install mode to install"
      # detect_update_install_mode: is done after docker_install_rippled is successful
      # stop_all_networks: is done after docker_install_rippled is successful
      docker_install_rippled true "${install}"
    fi
  fi
}

enable_feature() {
  l_enable_feature_opt="$1"
  feature="$2"

  feature_enabled=false
  if [ "${l_enable_feature_opt}" = "true" ]; then
    if [ -n "${feature}" ]; then
      for config_file in ${host_script_dir}/${RIPPLED_CONFIGS_FILE}
      do
        feature_configured=$(grep -w "${feature}" "${config_file}")
        if [ -z "${feature_configured}" ]; then
          feature_string="${RIPPLED_CONFIG_FEATURES_STANZA_NAME}\n${feature}"
          sed -i.bak "s/${RIPPLED_CONFIG_FEATURES_STANZA_NAME}/${feature_string}/g" "${config_file}"
          feature_enabled=true
        fi
      done

      if [ "${feature_enabled}" = "true" ]; then
        echo "- Feature '${feature}' enabled"
        stop_all_networks
        echo "  Please restart required networks"
      else
        echo "- Feature '${feature}' already enabled"
      fi
    else
      echo "Missing parameter <feature name>"
      exit 1
    fi
  fi
}

disable_feature() {
  l_disable_feature_opt="$1"
  feature="$2"

  feature_disabled=false
  if [ "${l_disable_feature_opt}" = "true" ]; then
    if [ -n "${feature}" ]; then
      for config_file in ${host_script_dir}/${RIPPLED_CONFIGS_FILE}
      do
        feature_configured=$(grep -w "${feature}" "${config_file}")
        if [ -n "${feature_configured}" ]; then
          feature_string=""
          sed -i.bak "/${feature}/d" "${config_file}"
          feature_disabled=true
        fi
      done

      if [ "${feature_disabled}" = "true" ]; then
        echo "- Feature '${feature}' disabled"
        stop_all_networks
        echo "  Please restart required networks"
      else
        echo "- Feature '${feature}' already disabled"
      fi
    else
      echo "Missing parameter <feature name>. Check help"
      exit 1
    fi
  fi
}

clean() {
  clean_opt="$1"
  if [ "${clean_opt}" = "true" ]; then
    echo "- Clean up Claudia"
    docker rm -f $(docker ps -aq --filter ancestor=${RIPPLED_NODE_CONTAINER_NAME}) > /dev/null 2>&1
    docker rmi -f ${RIPPLED_NODE_CONTAINER_NAME} > /dev/null 2>&1
    docker rm -f $(docker ps -aq --filter name=${WITNESS_SERVER_CONTAINER_NAME}) > /dev/null 2>&1
    docker rmi -f ${WITNESS_SERVER_CONTAINER_NAME} > /dev/null 2>&1
    rm -f "${INSTALL_MODE_FILE}" > /dev/null 2>&1
    rm -rf $HOME/logs > /dev/null 2>&1
    rm -rf $HOME/rippled_log > /dev/null 2>&1
    rm -rf $HOME/rippled_db > /dev/null 2>&1
    rm -f ${RIPPLED_REPO_BUILT} > /dev/null 2>&1
    rm -f ${WITNESS_REPO_BUILT} > /dev/null 2>&1

  fi
}

