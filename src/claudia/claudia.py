import os
import os.path
import subprocess

import click
import inquirer
from claudia.python.lib.framework.common import read_env_var
from inquirer.themes import GreenPassion

from claudia.versions import XRPL_PY_VERSION, XRPL_JS_VERSION


class SingletonClass(object):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(SingletonClass, cls).__new__(cls)
        return cls.instance


singleton = SingletonClass()
singleton.PROJECT_ROOT_DIR = os.path.dirname(__file__)


def set_to_js_wd():
    os.chdir("{}/javascript/".format(singleton.PROJECT_ROOT_DIR))


def set_to_py_wd():
    os.chdir("{}/python/".format(singleton.PROJECT_ROOT_DIR))


def set_to_project_root_wd():
    os.chdir(singleton.PROJECT_ROOT_DIR)


def compose_feature_helper_message():
    message = "Feature file to be used for the test run. Allowed values are "
    features = get_feature_file_names()
    for i in range(0, len(features)):
        message += "'{}', ".format(features[i])
    message += "and 'all' and is defaulted to 'payments'. \n\nMore information: https://behave.readthedocs.io/en/latest/tutorial.html?highlight=feature#feature-files."
    return message


def get_feature_file_names():
    set_to_project_root_wd()
    files = os.listdir('./features/')
    features = []
    for i in range(0, len(files)):
        features.append(files[i].replace(".feature", ""))

    return features


@click.group()
@click.version_option(message=f'%(prog)s version %(version)s\n  - Supports:\n    - XRPL-py v{XRPL_PY_VERSION}\n    - XRPL.js v{XRPL_JS_VERSION}')
def main():
    """Claudia says hi! Please choose a command to perform an action. A command can have multiple sub-commands and options. Use '--help' option for more information."""


@main.command()
def ui():
    """Launch Claudia UI"""
    try:
        clear_screen()
        launch_claudia_ui()
    except Exception as e:
        pass


def launch_claudia_ui():
    create_streamlit_credentials()
    set_to_project_root_wd()
    command = "streamlit run ui/claudia_ui.py"
    return subprocess.call(command, shell=True)


def create_streamlit_credentials():
    credentials_file = os.path.expanduser("~/.streamlit/credentials.toml")
    if not os.path.isfile(credentials_file):
        os.makedirs(os.path.dirname(credentials_file), exist_ok=True)
        f = open(credentials_file, 'w')
        f.write('[general]\nemail = ""\n')


@main.command()
def demo():
    """Launch claudia in demo mode"""
    try:
        clear_screen()
        launch_main_menu()
    except Exception as e:
        pass


def launch_main_menu():
    questions = [
        inquirer.List(
            "main_menu",
            message="Welcome to Claudia Demo! Please use ↑ ↓ and ↵ keys to choose an option. Current Selection",
            choices=[
                "Custom XRPL Networks",
                "XRPL Tests",
                "Settings",
                "Launch Claudia UI",
                "Exit"
            ],
        ),
    ]

    selection_text = inquirer.prompt(questions, theme=GreenPassion())['main_menu']

    if selection_text == "Custom XRPL Networks":
        clear_screen()
        launch_custom_rippled_networks_menu()
    elif selection_text == "XRPL Tests":
        clear_screen()
        launch_test_task_menu()
    elif selection_text == "Settings":
        clear_screen()
        launch_settings_menu()
    elif selection_text == "Launch Claudia UI":
        clear_screen()
        launch_claudia_ui()
    elif selection_text == 'Exit':
        print("Thank you for using Claudia demo. Bye!")
        return


def launch_custom_rippled_networks_menu():
    relaunch_wizard = True
    questions = [
        inquirer.List(
            "rippled_task_menu",
            message="Here you can find a list of rippled related tasks. Please use ↑ ↓ and ↵ keys to choose an option. Current Selection",
            choices=[
                "Build rippled from local code",
                "Install rippled",
                "Start local-mainnet",
                "Stop local-mainnet",
                "Check local-mainnet status",
                "Build witness server",
                "Start local-sidechain",
                "Stop local-sidechain",
                "Check witness server status",
                "Back to main menu"
            ],
        ),
    ]

    selection_text = inquirer.prompt(questions, theme=GreenPassion())['rippled_task_menu']
    if selection_text == "Build rippled from local code":
        relaunch_wizard = False
        repo_path = get_valid_repo_path()
        if repo_path == "" or repo_path.replace("'", "").replace('"', '').lower() == 'back':
            relaunch_wizard = True
        else:
            clear_screen()
            print("\nINFO: In order to '{}', run: 'claudia rippled build --repo <absolute_path_to_local_repo>'".format(
                selection_text))
            print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
            launch_command_rippled_build(repo_path)
    elif selection_text == 'Install rippled':
        relaunch_wizard = False
        clear_screen()
        rippled_branch = get_rippled_branch()
        if rippled_branch == "" or rippled_branch.replace("'", "").replace('"', '').lower() == 'back':
            relaunch_wizard = True
        else:
            clear_screen()
            print("\nINFO: In order to '{}', run: 'claudia rippled install --rippled_branch <branch_name>'".format(
                selection_text))
            print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
            launch_command_rippled_install(rippled_branch)
    elif selection_text == 'Start local-mainnet':
        relaunch_wizard = False
        clear_screen()
        print("\nINFO: In order to '{}', run: 'claudia local-mainnet start'".format(selection_text))
        print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
        launch_command_network_start()
    elif selection_text == 'Check local-mainnet status':
        relaunch_wizard = False
        clear_screen()
        print("\nINFO: In order to '{}', run: 'claudia local-mainnet status'".format(selection_text))
        print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
        launch_command_network_status()
    elif selection_text == 'Stop local-mainnet':
        relaunch_wizard = False
        clear_screen()
        print("\nINFO: In order to '{}', run: 'claudia local-mainnet stop'".format(selection_text))
        print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
        launch_command_network_stop()
    elif selection_text == 'Build witness server':
        relaunch_wizard = False
        repo_path = get_valid_repo_path()
        if repo_path == "" or repo_path.replace("'", "").replace('"', '').lower() == 'back':
            relaunch_wizard = True
        else:
            clear_screen()
            print("\nINFO: In order to '{}', run: 'claudia witness build --repo <absolute_path_to_local_repo>'".format(
                selection_text))
            print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
            launch_command_witness_build(repo_path)
    elif selection_text == 'Check witness server status':
        relaunch_wizard = False
        clear_screen()
        print("\nINFO: In order to '{}', run: 'claudia witness status'".format(selection_text))
        print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
        launch_command_witness_status()
    elif selection_text == 'Start local-sidechain':
        relaunch_wizard = False
        clear_screen()
        print("\nINFO: In order to '{}', run: 'claudia local-sidechain start'".format(selection_text))
        print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
        launch_command_sidechain_start()
    elif selection_text == 'Stop local-sidechain':
        relaunch_wizard = False
        clear_screen()
        print("\nINFO: In order to '{}', run: 'claudia local-sidechain stop'".format(selection_text))
        print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
        launch_command_sidechain_stop()
    elif selection_text == 'Back to main menu':
        clear_screen()
        launch_main_menu()
        return

    if relaunch_wizard:
        clear_screen()
        launch_custom_rippled_networks_menu()
    else:
        if get_confirmation("Would you like to continue with the demo?"):
            clear_screen()
            launch_custom_rippled_networks_menu()
        else:
            print("Thank you for using Claudia demo. Bye!")
            return


def launch_test_task_menu():
    relaunch_wizard = True
    questions = [
        inquirer.List(
            "test_task_menu",
            message="Here you can find a list of test related tasks. Please use ↑ ↓ and ↵ keys to choose an option. Current Selection",
            choices=[
                "Run system tests",
                "Run unit tests",
                "Back to main menu"
            ],
        ),
    ]

    selection_text = inquirer.prompt(questions, theme=GreenPassion())['test_task_menu']
    if selection_text == 'Run system tests':
        relaunch_wizard = False
        clear_screen()
        print("\nINFO: In order to '{}', run: 'claudia run systemtests'".format(selection_text))
        print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
        client_type = 'websocket'
        invalidate_cache = 'false'
        feature_files = get_feature_file_names()
        feature_files.append('all')
        lib = inquirer.prompt(
            [inquirer.List("confirmation", message="Please choose library type. Current Selection",
                           choices=["py", "js"], default="py")],
            theme=GreenPassion()
        )['confirmation']
        if lib == 'py':
            client_type = inquirer.prompt(
                [inquirer.List("confirmation", message="Please choose client type. Current Selection",
                               choices=["websocket", "jsonrpc"], default="websocket")],
                theme=GreenPassion()
            )['confirmation']
        network = inquirer.prompt(
            [inquirer.List("confirmation", message="Please choose network type. Current Selection",
                           choices=["local-mainnet", "devnet", "testnet", "local-sidechain"],
                           default="local-mainnet")],
            theme=GreenPassion()
        )['confirmation']

        tag = inquirer.prompt(
            [inquirer.List("confirmation", message="Please choose tag. Current Selection",
                           choices=['smoke', 'regression', 'time_intensive'], default="smoke")],
            theme=GreenPassion()
        )['confirmation']

        feature = inquirer.prompt(
            [inquirer.List("confirmation",
                           message="Please choose the feature file. Choose 'all' to include all feature files. Current Selection",
                           choices=feature_files, default="payments")],
            theme=GreenPassion()
        )['confirmation']

        if lib == 'js':
            invalidate_cache = inquirer.prompt(
                [inquirer.List("confirmation",
                               message="Please choose if you would like to destroy cache, if any. Current Selection",
                               choices=["false", "true"], default="false")],
                theme=GreenPassion()
            )['confirmation']

        launch_command_run_system_tests(lib, client_type, network, tag, feature, invalidate_cache)

    elif selection_text == 'Run unit tests':
        relaunch_wizard = False
        print("\nINFO: In order to '{}', run: 'claudia run unittests'".format(selection_text))
        print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
        testname = get_testname()
        if testname.replace("'", "").replace('"', '').lower() == 'back':
            relaunch_wizard = True
        else:
            launch_command_run_unit_tests(testname)
    elif selection_text == 'Back to main menu':
        clear_screen()
        launch_main_menu()
        return

    if relaunch_wizard:
        clear_screen()
        launch_test_task_menu()
    else:
        if get_confirmation("Would you like to continue with the demo?"):
            clear_screen()
            launch_test_task_menu()
        else:
            print("Thank you for using Claudia demo. Bye!")
            return


def launch_command_run_system_tests(lib, client_type, network, tag, feature, invalidate_cache):
    try:
        click.echo("INFO: Navigate to '{}' to view explorer.\n".format(get_explorer_url(network)))
        setup_system_test_env(lib, client_type, network, tag, feature, invalidate_cache)
        print("Setting CONNECTION_SCHEME='{}', CONNECTION_URL='{}' and CONNECTION_TYPE='{}'".format(
            read_env_var('CONNECTION_SCHEME'),
            read_env_var('CONNECTION_URL'),
            read_env_var('CONNECTION_TYPE'))
        )

        command = get_launch_command_system_test_tests(lib, tag, feature)
        subprocess.call(command, shell=True)
        teardown_system_test_env(lib)
    except Exception as e:
        set_to_project_root_wd()
        raise e


def launch_settings_menu():
    relaunch_wizard = True
    questions = [
        inquirer.List(
            "misc_task_menu",
            message="Here you can find a list of all the settings. Please use ↑ ↓ and ↵ keys to choose an option. Current Selection",
            choices=[
                "Set install mode as build",
                "Set install mode as install",
                "Enable a rippled feature",
                "Disable a rippled feature",
                "Clean up the host and free resources",
                "List system requirements (prerequisites)",
                "List system test features",
                "Print already built/installed rippled version",
                "Back to main menu"
            ],
        ),
    ]

    selection_text = inquirer.prompt(questions, theme=GreenPassion())['misc_task_menu']
    if selection_text == 'List system test features':
        relaunch_wizard = False
        clear_screen()
        print("\nINFO: In order to '{}', run: 'claudia list system-test-features'".format(selection_text))
        print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
        launch_command_system_test_features()
    elif selection_text == 'List system requirements (prerequisites)':
        relaunch_wizard = False
        clear_screen()
        print("\nINFO: In order to '{}', run: 'claudia list system-requirements'".format(selection_text))
        print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
        launch_command_system_requirements()
    elif selection_text == 'Set install mode as build':
        relaunch_wizard = False
        clear_screen()
        print("\nINFO: In order to '{}', run: 'claudia set-install-mode build'".format(selection_text))
        print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
        launch_command_set_install_mode_to_build()
    elif selection_text == 'Set install mode as install':
        relaunch_wizard = False
        clear_screen()
        print("\nINFO: In order to '{}', run: 'claudia set-install-mode install'".format(selection_text))
        print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
        launch_command_set_install_mode_to_install()
    elif selection_text == 'Enable a rippled feature':
        relaunch_wizard = False
        clear_screen()
        print("\nINFO: In order to '{}', run: 'claudia enable-feature --feature <feature_name>'".format(selection_text))
        print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
        feature_name = get_feature_name()
        if feature_name == "" or feature_name.replace("'", "").replace('"', '').lower() == 'back':
            relaunch_wizard = True
        else:
            launch_command_enable_feature(feature_name)
    elif selection_text == 'Disable a rippled feature':
        relaunch_wizard = False
        clear_screen()
        print("\nINFO: In order to '{}', run: 'claudia disable-feature --feature <feature_name>'".format(
            selection_text
        ))
        print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
        feature_name = get_feature_name()
        if feature_name == "" or feature_name.replace("'", "").replace('"', '').lower() == 'back':
            relaunch_wizard = True
        else:
            launch_command_disable_feature(feature_name)
    elif selection_text == 'Clean up the host and free resources':
        relaunch_wizard = False
        clear_screen()
        print("\nINFO: In order to '{}', run: 'claudia clean'".format(selection_text))
        print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
        launch_command_clean()
    elif selection_text == 'Print already built/installed rippled version'.format(selection_text):
        relaunch_wizard = False
        clear_screen()
        print("\nINFO: In order to '{}', run: 'claudia rippled version'".format(selection_text))
        print("You have opted to execute '{}'. Starting now...\n".format(selection_text))
        launch_command_rippled_version()
    elif selection_text == 'Back to main menu':
        clear_screen()
        launch_main_menu()
        return

    if relaunch_wizard:
        clear_screen()
        launch_settings_menu()
    else:
        if get_confirmation("Would you like to continue with the demo?"):
            clear_screen()
            launch_settings_menu()
        else:
            print("Thank you for using Claudia demo. Bye!")
            return


def get_valid_repo_path():
    input_path = [
        inquirer.Text('repo path',
                      message="Please enter the absolute path to the rippled repo. Type 'back' or simply press ↵ (return) key to skip and go back to main menu.")
    ]
    full_repo_path = inquirer.prompt(input_path, theme=GreenPassion())['repo path']
    if full_repo_path == "" or full_repo_path == "back":
        pass
    else:
        if not os.path.isabs(full_repo_path) or not os.path.exists(full_repo_path):
            print(
                "The rippled repository path '{}' is not correct. Please provide correct absolute path!".format(
                    full_repo_path))
            return get_valid_repo_path()

    return full_repo_path

def get_rippled_branch():
    rippled_branch = inquirer.prompt(
        [inquirer.List("rippled_branch", message="Please choose rippled branch. Current Selection",
                       choices=["master", "develop", "release"], default="master")],
        theme=GreenPassion()
    )['rippled_branch']
    return rippled_branch


def get_testname():
    testname = [
        inquirer.Text('testname',
                      message="Please enter name test name. Press ↵ (return) key to include run everything. Type 'back' to skip and go back to main menu.")
    ]
    return inquirer.prompt(testname, theme=GreenPassion())['testname']


def get_feature_name():
    feature_name = [
        inquirer.Text('feature_name',
                      message="Please enter the feature name. Type 'back' or simply press ↵ (return) key to skip and go back to main menu.")
    ]
    return inquirer.prompt(feature_name, theme=GreenPassion())['feature_name']


def get_confirmation(confirmation_message):
    q = [inquirer.List("confirmation", message=confirmation_message, choices=["Yes", "No"], default="No")]
    answer = inquirer.prompt(q, theme=GreenPassion())['confirmation']
    if answer == 'Yes':
        return_value = True
    else:
        return_value = False
    return return_value


def clear_screen():
    if os.name == 'posix':
        os.system('clear')
    elif os.name == 'nt':
        os.system('cls')


@main.group()
def rippled():
    """Build or install rippled"""


@main.group()
def local_mainnet():
    """Setup rippled Network"""


@main.group()
def local_sidechain():
    """Setup Sidechain"""


@main.group()
def witness():
    """Setup Witness Server for Sidechain"""


@main.group()
def set_install_mode():
    """Setup Install Mode"""


@main.group()
@click.pass_context
def run(context):
    """Run XRPL automated tests"""


@main.command()
def clean():
    """Clean up the host and free resources"""
    launch_command_clean()


def launch_command_clean(ask_confirmation=True):
    if ask_confirmation:
        print("WARNING!! Running this command will wipe out everything built by Claudia. This action cannot be undone.")
        input("Press enter to continue or ctrl+c to cancel...")

    command = get_launch_command_clean()
    return subprocess.call(command, shell=True)


def get_launch_command_clean():
    set_to_project_root_wd()
    return "sh network_setup/setup.sh --clean"


@main.command()
@click.option('--feature', required=True, help="The rippled feature name")
def enable_feature(feature):
    """Enable rippled feature"""
    launch_command_enable_feature(feature)


def launch_command_enable_feature(feature):
    command = get_launch_command_enable_feature(feature)
    return subprocess.call(command, shell=True)


def get_launch_command_enable_feature(feature):
    set_to_project_root_wd()
    return "sh network_setup/setup.sh --enableFeature {}".format(feature)


@main.command()
@click.option('--feature', required=True, help="The rippled feature name")
def disable_feature(feature):
    """Disable rippled feature"""
    launch_command_disable_feature(feature)


def launch_command_disable_feature(feature):
    command = get_launch_command_disable_feature(feature)
    return subprocess.call(command, shell=True)


def get_launch_command_disable_feature(feature):
    set_to_project_root_wd()
    return "sh network_setup/setup.sh --disableFeature {}".format(feature)


@main.group()
def list():
    """List supported options"""


@list.command()
def system_test_features():
    """List all supported features to be tested"""
    launch_command_system_test_features()


def launch_command_system_test_features():
    click.echo(get_launch_command_system_test_features_message())


def get_launch_command_system_test_features_message():
    set_to_project_root_wd()
    features = os.listdir('./features/')
    message = "Following features were found:\n"
    for i in range(0, len(features)):
        message += "   - {}\n".format(features[i].replace(".feature", ""))
    return message


@local_sidechain.command()
def start():
    """Start a new sidechain"""
    launch_command_sidechain_start()


def launch_command_sidechain_start():
    command = get_launch_command_sidechain_start()
    return subprocess.call(command, shell=True)


def get_launch_command_sidechain_start():
    set_to_project_root_wd()
    return "sh network_setup/setup.sh --sidechainStart"


@local_sidechain.command()
def stop():
    """Stop sidechain"""
    launch_command_sidechain_stop()


def launch_command_sidechain_stop():
    command = get_launch_command_sidechain_stop()
    return subprocess.call(command, shell=True)


def get_launch_command_sidechain_stop():
    set_to_project_root_wd()
    return "sh network_setup/setup.sh --sidechainStop"


@witness.command()
@click.option('--repo', required=True, help="The path to a local witness server repo")
def build(repo):
    """Build witness server"""
    launch_command_witness_build(repo)


def launch_command_witness_build(repo):
    if not os.path.isabs(repo) or not os.path.exists(repo):
        click.echo(
            " - ERROR: The rippled repository path '{}' is not correct. Please provide correct absolute path!".format(repo))
        return

    command = get_launch_command_witness_build(repo)
    return subprocess.call(command, shell=True)


def get_launch_command_witness_build(repo):
    set_to_project_root_wd()
    return "sh network_setup/setup.sh --witnessBuild --repo {}".format(repo)


@witness.command()
def status():
    """Witness server status"""
    launch_command_witness_status()


def launch_command_witness_status():
    command = get_launch_command_witness_status()
    return subprocess.call(command, shell=True)


def get_launch_command_witness_status():
    set_to_project_root_wd()
    return "sh network_setup/setup.sh --witnessStatus"


def get_launch_command_deploy_network(count):
    set_to_project_root_wd()
    return f"sh aws/setup.sh --deployNetwork --nodeCount {count}"


@set_install_mode.command()
def build():
    """Set install mode to build"""
    launch_command_set_install_mode_to_build()


def launch_command_set_install_mode_to_build():
    command = get_launch_command_set_install_mode_to_build()
    return subprocess.call(command, shell=True)


def get_launch_command_set_install_mode_to_build():
    set_to_project_root_wd()
    return "sh network_setup/setup.sh --setInstallMode build"


@set_install_mode.command()
def install():
    """Set install mode to install"""
    launch_command_set_install_mode_to_install()


def launch_command_set_install_mode_to_install():
    command = get_launch_command_set_install_mode_to_install()
    return subprocess.call(command, shell=True)


def get_launch_command_set_install_mode_to_install():
    set_to_project_root_wd()
    return "sh network_setup/setup.sh --setInstallMode install"


@list.command()
def system_requirements():
    """List all system requirements before continuing further with claudia"""
    launch_command_system_requirements()


def launch_command_system_requirements():
    click.echo(get_launch_command_system_requirements_message())


def get_launch_command_system_requirements_message():
    message = """
    1. Common requirements:
        - Python3
        - pip
        - docker
    2. Pull down a fresh copy of rippled code base from https://github.com/XRPLF/rippled
    3. Optional: Following depedencies are only required if you intend to run Javascript tests:
        - node
        - npm
    
        More detailed information can be found under the 'General prerequisite' section here: https://pypi.org/project/claudia
    """
    return message


@rippled.command()
@click.option('--repo', required=True, help="The path to a local rippled repo")
def build(repo):
    """Build rippled from source"""
    launch_command_rippled_build(repo)


def launch_command_rippled_build(repo):
    if not os.path.isabs(repo) or not os.path.exists(repo):
        click.echo(
            " - ERROR: The rippled repository path '{}' is not correct. Please provide correct absolute path!".format(repo))
        return
    command = get_launch_command_rippled_build(repo)
    return subprocess.call(command, shell=True)


def get_launch_command_rippled_build(repo):
    set_to_project_root_wd()
    return "sh network_setup/setup.sh --rippledBuild --repo {}".format(repo)


@rippled.command()
def version():
    """View rippled version info"""
    launch_command_rippled_version()


def launch_command_rippled_version():
    command = get_launch_command_rippled_version()
    return subprocess.call(command, shell=True)


def get_launch_command_rippled_version():
    set_to_project_root_wd()
    return "sh network_setup/setup.sh --rippledVersion"


@rippled.command()
@click.option('--rippled_branch', default='master', help="Source branch for rippled binaries")
def install(rippled_branch):
    """Install rippled packages"""
    launch_command_rippled_install(rippled_branch)


def launch_command_rippled_install(rippled_branch):
    if rippled_branch not in ['master', 'develop', 'release']:
        print(f"The rippled branch '{rippled_branch}' is not correct. Allowed values are master, develop and release (case-sensitive).")
        return
    command = get_launch_command_rippled_install(rippled_branch)
    return subprocess.call(command, shell=True)


def get_launch_command_rippled_install(rippled_branch):
    set_to_project_root_wd()
    return f"sh network_setup/setup.sh --rippledInstall --rippledBranch {rippled_branch}"


@local_mainnet.command()
def start():
    """Start a new rippled network"""
    launch_command_network_start()


def launch_command_network_start():
    command = get_launch_command_network_start()
    return subprocess.call(command, shell=True)


def get_launch_command_network_start():
    set_to_project_root_wd()
    return "sh ./network_setup/setup.sh --networkStart"


@local_mainnet.command()
def stop():
    """Stop rippled network"""
    launch_command_network_stop()


def launch_command_network_stop():
    command = get_launch_command_sidechain_stop()
    return subprocess.call(command, shell=True)


def get_launch_command_network_stop():
    set_to_project_root_wd()
    return "sh ./network_setup/setup.sh --networkStop"


@local_mainnet.command()
def status():
    """rippled network status"""
    launch_command_network_status()


def launch_command_network_status():
    command = get_launch_command_network_status()
    return subprocess.call(command, shell=True)


def get_launch_command_network_status():
    set_to_project_root_wd()
    return "sh ./network_setup/setup.sh --networkStatus"


def get_explorer_url(network):
    url = ""
    if network == 'testnet':
        url = "https://testnet.xrpl.org"
    elif network == 'devnet':
        url = "https://devnet.xrpl.org"
    elif network == "local-sidechain":
        url = "https://custom.xrpl.org/localhost:6003"
    else:
        url = "https://custom.xrpl.org/localhost:6001"

    return url


@run.command()
@click.pass_context
@click.option('--lib', default='py',
              help="The type of client library to be used for running the tests. Allowed values are 'py' and 'js' and is defaulted to 'py'.  \n\nMore information: https://xrpl.org/client-libraries.html#client-libraries")
@click.option('--client_type', default='websocket',
              help="The type of client to be used. This flag should only be used with 'py' library. Allowed values are 'websocket' and 'jsonrpc' and is defaulted to 'websocket'.  \n\nMore information: https://xrpl.org/get-started-using-http-websocket-apis.html#differences-between-json-rpc-and-websocket")
@click.option('--network', default='local-mainnet',
              help="The type of network to be used. Allowed values are 'devnet', 'testnet', 'local-mainnet', and 'local-sidechain'; and is defaulted to 'local-mainnet'.  \n\nMore information: https://xrpl.org/get-started-using-http-websocket-apis.html#differences-between-json-rpc-and-websocket")
@click.option('--tag', default='smoke',
              help="Tag name of the all the tests to be included in the test run. Allowed values are 'smoke', 'regression' and 'time_intensive' and is defaulted to 'smoke'.  \n\nMore information: https://behave.readthedocs.io/en/latest/tag_expressions.html")
@click.option('--feature', default='payments',
              help=compose_feature_helper_message())
@click.option('--invalidate_cache', default='false',
              help="Forces ignoring cache, and reinstalling dependencies. This flag should only be used with 'js' library. Allowed values are 'true' and 'false' and is defaulted to 'false'.")
def systemtests(context, lib, client_type, network, tag, feature, invalidate_cache):
    """Launch XRPL system tests using XRPL client library"""
    launch_command_run_system_tests(lib, client_type, network, tag, feature, invalidate_cache)


def setup_system_test_env(lib, client_type, network, tag, feature, invalidate_cache):
    if lib == 'py':
        if invalidate_cache != 'false':
            raise Exception("--invalidate_cache flag is supported not with {} library client.".format(lib))
        set_to_py_wd()
        set_python_launch_vars(network, client_type)
        load_feature_files()
    elif lib == 'js':
        if client_type != 'websocket':
            raise Exception("Client Type {} is not supported with {} library client.".format(client_type, lib))
        set_to_js_wd()
        if invalidate_cache != 'false':
            click.echo("Invalidating cache...")
            command = "rm -rf ./node_modules"
            subprocess.call(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        install_js_dependencies()
        set_javascript_launch_vars(network)
        load_feature_files()
    else:
        raise Exception("Invalid library type: {}".format(lib))


def get_launch_command_system_test_tests(lib, tag, feature):
    if lib == 'py':
        if feature == "all":
            command = "behave --no-skipped --tags={}".format(tag)
        else:
            command = "behave --no-skipped --tags={} ./features/{}.feature".format(tag, feature)
    elif lib == 'js':
        if feature == "all":
            command = "npx cucumber-js --format @cucumber/pretty-formatter --tags @{}".format(tag)
        else:
            command = "npx cucumber-js --format @cucumber/pretty-formatter --tags @{} ./features/{}.feature".format(
                tag,
                feature
            )
    return command


def teardown_system_test_env(lib):
    if lib == 'py':
        unload_feature_files()
        set_to_project_root_wd()
    elif lib == 'js':
        unload_feature_files()
        set_to_project_root_wd()
    else:
        raise Exception("Invalid library type: {}".format(lib))


@run.command()
@click.option('--testname', default='everything',
              help="The unit test which needs to be selected. If not provided, all tests are selected.")
def unittests(testname):
    """Launch rippled unit tests"""
    launch_command_run_unit_tests(testname)


def launch_command_run_unit_tests(testname):
    command = get_launch_command_run_unit_tests(testname)
    return subprocess.call(command, shell=True)


def get_launch_command_run_unit_tests(testname):
    set_to_project_root_wd()
    if testname == '':
        return "sh network_setup/setup.sh --runUnittests"
    else:
        return "sh network_setup/setup.sh --runUnittests {}".format(testname)


def set_python_launch_vars(network, client_type):
    if network == "local-mainnet":
        if client_type == "websocket":
            connectionScheme = "ws"
            connectionURL = "127.0.0.1:6001"
            connectionType = "websocket"
        elif client_type == "jsonrpc":
            connectionScheme = "http"
            connectionURL = "127.0.0.1:5001"
            connectionType = "jsonrpc"
        else:
            raise Exception("{} is not a valid client_type".format(client_type))
    elif network == "local-sidechain":
        if client_type == "websocket":
            connectionScheme = "ws"
            connectionURL = "127.0.0.1:6003"
            connectionType = "websocket"
        elif client_type == "jsonrpc":
            connectionScheme = "http"
            connectionURL = "127.0.0.1:5003"
            connectionType = "jsonrpc"
        else:
            raise Exception("{} is not a valid client_type".format(client_type))
    elif network == "devnet":
        if client_type == "websocket":
            connectionScheme = "wss"
            connectionURL = "s.devnet.rippletest.net:51233"
            connectionType = "websocket"
        elif client_type == "jsonrpc":
            connectionScheme = "https"
            connectionURL = "s.devnet.rippletest.net:51234"
            connectionType = "jsonrpc"
        else:
            raise Exception("{} is not a valid client_type".format(client_type))
    elif network == "testnet":
        if client_type == "websocket":
            connectionScheme = "wss"
            connectionURL = "s.altnet.rippletest.net:51233"
            connectionType = "websocket"
        elif client_type == "jsonrpc":
            connectionScheme = "https"
            connectionURL = "s.altnet.rippletest.net:51234"
            connectionType = "jsonrpc"
        else:
            raise Exception("{} is not a valid client_type".format(client_type))
    else:
        raise Exception("{} is not a valid network".format(network))

    os.environ['CONNECTION_SCHEME'] = connectionScheme
    os.environ['CONNECTION_URL'] = connectionURL
    os.environ['CONNECTION_TYPE'] = connectionType


def set_javascript_launch_vars(network):
    if network == "local-mainnet":
        connectionScheme = "ws"
        connectionURL = "127.0.0.1:6001"
        connectionType = "websocket"
    elif network == "local-sidechain":
        connectionScheme = "ws"
        connectionURL = "127.0.0.1:6003"
        connectionType = "websocket"
    elif network == "devnet":
        connectionScheme = "wss"
        connectionURL = "s.devnet.rippletest.net:51233"
        connectionType = "websocket"
    elif network == "testnet":
        connectionScheme = "wss"
        connectionURL = "s.altnet.rippletest.net:51233"
        connectionType = "websocket"
    else:
        raise Exception("{} is not a valid network".format(network))

    os.environ['CONNECTION_SCHEME'] = connectionScheme
    os.environ['CONNECTION_URL'] = connectionURL
    os.environ['CONNECTION_TYPE'] = connectionType


def load_feature_files():
    unload_feature_files()
    os.popen("cp -fr ../features/*.feature ./features")


def unload_feature_files():
    os.popen("rm -rf ./features/*.feature")


def launch_behave(tag, feature):
    if feature == "all":
        command = "behave --no-skipped --tags={}".format(tag)
    else:
        command = "behave --no-skipped --tags={} ./features/{}.feature".format(tag, feature)
    return subprocess.call(command, shell=True)


def install_js_dependencies():
    command = "sh ./runSetup"
    return subprocess.call(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def launch_cucumber(tag, feature):
    if feature == "all":
        command = "npx cucumber-js --format @cucumber/pretty-formatter --tags @{}".format(tag)
    else:
        command = "npx cucumber-js --format @cucumber/pretty-formatter --tags @{} ./features/{}.feature".format(tag,
                                                                                                                feature)
    return subprocess.call(command, shell=True)


if __name__ == '__main__':
    main(context, obj={})
