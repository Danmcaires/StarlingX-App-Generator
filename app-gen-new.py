import yaml
import os
import sys, getopt, getpass
import subprocess
import hashlib
import tarfile
import re
import shutil
from urllib import request

SCHEMA_KUSTOMIZATION_TEMPLATE = 'templates_flux/kustomization.template'
SCHEMA_BASE_TEMPLATES = 'templates_flux/base/'
SCHEMA_MANIFEST_TEMPLATE = 'templates_flux/fluxcd-manifest'
SCHEMA_COMMON_TEMPLATE = 'templates_plugins/common.template'
SCHEMA_HELM_TEMPLATE = 'templates_plugins/helm.template'
TEMP_USER_DIR = '/tmp/' + getpass.getuser() + '/'
# Temp app work dir to hold git repo and upstream tarball
# TEMP_APP_DIR = TEMP_USER_DIR/appName
TEMP_APP_DIR = ''
APP_GEN_PY_PATH = os.path.split(os.path.realpath(__file__))[0]

def to_camel_case(s):
    return s[0].lower() + s.title().replace('_','')[1:] if s else s

class FluxApplication:

    def __init__(self, app_data):

        # Initialize application config
        self._flux_manifest = {}

        # Initialize manifest
        self._flux_manifest['appName'] = app_data['appName']
        self._flux_manifest['namespace'] = app_data['namespace']

        # Initialize chartgroup
        self._flux_chartgroup = app_data['chartGroup']
        self._flux_chartgroup[0]['namespace'] = self._flux_manifest['namespace']

        # Initialize chart
        self._flux_chart = app_data['chart']
        for i in range(len(self._flux_chart)):
            self._flux_chart[i]['namespace'] = self._flux_manifest['namespace']


    def get_app_name(self):
        return self._flux_manifest['appName']


    # pyyaml does not support writing yaml block with initial indent
    # add initial indent for yaml block substitution
    def _write_yaml_to_manifest(self, key, src, init_indent):
        target = {}
        # add heading key
        target[key] = src
        lines = yaml.safe_dump(target).split('\n')
        # remove ending space ans first line
        lines.pop()
        lines.pop(0)
        indents = ' ' * init_indent
        for i in range(len(lines)):
            lines[i] = indents + lines[i]
        # restore ending '\n'
        return '\n'.join(lines) + '\n'


    def _substitute_values(self, in_line, dicts):
        out_line = in_line
        pattern = re.compile('\$.+?\$')
        results = pattern.findall(out_line)
        if results:
            for result in results:
                result_word = result.strip('$').split('%')
                value_key = result_word[0]
                value_default = ''
                if len(result_word) > 1:
                    value_default = result_word[1]
                # underscore case to camel case
                value = to_camel_case(value_key)
                if value in dicts:
                    out_line = out_line.replace(result, str(dicts[value]))
                elif value_default:
                    out_line = out_line.replace(result, value_default)

        if out_line == in_line:
            return out_line, False
        else:
            return out_line, True


    def _substitute_blocks(self, in_line, dicts):
        out_line = in_line
        result = re.search('@\S+\|\d+@',out_line)
        if result:
            block_key = result.group().strip('@').split('|')
            key = block_key[0].lower()
            indent = int(block_key[1])
            if key in dicts:
                out_line = self._write_yaml_to_manifest(key, dicts[key], indent)
            else:
                out_line = ''

        return out_line


    # Sub-process of app generation
    # generate application fluxcd manifest files
    #
    def _gen_fluxcd_manifest(self):
        # check manifest file existance
        flux_dir = self._flux_manifest['outputFluxDir']

        # update schema path to abspath
        kustomization_template = APP_GEN_PY_PATH + '/' + SCHEMA_KUSTOMIZATION_TEMPLATE
        
        base_helmrepo_template = APP_GEN_PY_PATH + '/' + SCHEMA_BASE_TEMPLATES + '/helmrepository.template'
        base_kustom_template = APP_GEN_PY_PATH + '/' + SCHEMA_BASE_TEMPLATES + '/kustomization.template'
        base_namespace_template = APP_GEN_PY_PATH + '/' + SCHEMA_BASE_TEMPLATES + '/namespace.template'

        manifest_helmrelease_template = APP_GEN_PY_PATH + '/' + SCHEMA_MANIFEST_TEMPLATE + '/helmrelease.template'
        manifest_kustomization_template = APP_GEN_PY_PATH + '/' + SCHEMA_MANIFEST_TEMPLATE + '/kustomization.template'

        manifest = self._flux_manifest
        chartgroup = self._flux_chartgroup[0]
        chart = self._flux_chart

        # generate kustomization file
        try:
            with open(kustomization_template, 'r') as f:
                kustomization_schema = f.readlines()
        except IOError:
            print('File %s not found' % kustomization_template)
            return False
        kustom_file = flux_dir + 'kustomization.yaml'
        with open(kustom_file, 'a') as f:
            # substitute values
            for line in kustomization_schema:
                # substitute template values to manifest values
                out_line, substituted = self._substitute_values(line, chartgroup)
                if not substituted:
                    # substitute template blocks to manifest blocks
                    out_line = self._substitute_blocks(line, chartgroup)
                f.write(out_line)


        # generate base/namespace file
        try:
            with open(base_namespace_template, 'r') as f:
                base_namespace_schema = f.readlines()
        except IOError:
            print('File %s not found' % base_namespace_template)
            return False
        base_namespace_file = flux_dir + 'base/namespace.yaml'
        with open(base_namespace_file, 'a') as f:
            # substitute values
            for line in base_namespace_schema:
                # substitute template values to manifest values
                out_line, substituted = self._substitute_values(line, manifest)
                if not substituted:
                    # substitute template blocks to manifest blocks
                    out_line = self._substitute_blocks(line, manifest)
                f.write(out_line)


        # generate base/kustomization file
        # generate base/helmrepository file
        # Both yaml files don't need to add informations from the input file
        try:
            with open(base_kustom_template, 'r') as f:
                base_kustom_schema = f.readlines()
        except IOError:
            print('File %s not found' % base_kustom_template)
            return False
        base_kustom_file = flux_dir + 'base/kustomization.yaml'
        with open(base_kustom_file, 'a') as f:
            for line in base_kustom_schema:
                out_line = line
                f.write(out_line)

        try:
            with open(base_helmrepo_template, 'r') as f:
                base_helmrepo_schema = f.readlines()
        except IOError:
            print('File %s not found' % base_helmrepo_template)
            return False
        base_helmrepo_file = flux_dir + 'base/helmrepository.yaml'
        with open(base_helmrepo_file, 'a') as f:
            for line in base_helmrepo_schema:
                out_line = line
                f.write(out_line)


        # iterate each fluxcd_chart for the generation of its fluxcd manifests
        for idx in range(len(chart)):
            a_chart = chart[idx]

            # generate manifest/helmrelease file
            try:
                with open(manifest_helmrelease_template, 'r') as f:
                    manifest_helmrelease_schema = f.readlines()
            except IOError:
                print('File %s not found' % manifest_helmrelease_template)
                return False
            manifest_helmrelease_file = flux_dir + a_chart['name'] + '/helmrelease.yaml'
            with open(manifest_helmrelease_file, 'a') as f:
                # fetch chart specific info
                for line in manifest_helmrelease_schema:
                    # substitute template values to chart values
                    out_line, substituted = self._substitute_values(line, a_chart)
                    if not substituted:
                        # substitute template blocks to chart blocks
                        out_line = self._substitute_blocks(line, a_chart)
                    f.write(out_line)


            # generate manifest/kustomizaion file
            try:
                with open(manifest_kustomization_template, 'r') as f:
                    manifest_kustomization_schema = f.readlines()
            except IOError:
                print('File %s not found' % manifest_kustomization_template)
                return False            
            manifest_kustomization_file = flux_dir + a_chart['name'] + '/kustomization.yaml'
            with open(manifest_kustomization_file, 'a') as f:
                # fetch chart specific info
                for line in manifest_kustomization_schema:
                    # substitute template values to chart values
                    out_line, substituted = self._substitute_values(line, a_chart)
                    if not substituted:
                        # substitute template blocks to chart blocks
                        out_line = self._substitute_blocks(line, a_chart)
                    f.write(out_line)


            # generate an empty manifest/system-overrides file
            system_override_file = flux_dir + '/' + a_chart['name'] + '/' + a_chart['name'] + '-system-overrides.yaml'
            open(system_override_file, 'w').close()


            # generate a manifest/static-overrides file
            system_override_file = flux_dir + '/' + a_chart['name'] + '/' + a_chart['name'] + '-static-overrides.yaml'
            open(system_override_file, 'w').close()

        return True
    

    def _gen_plugins(self):

        plugin_dir =  self._flux_manifest['outputPluginDir']

        common_template = APP_GEN_PY_PATH + '/' + SCHEMA_COMMON_TEMPLATE
        helm_template = APP_GEN_PY_PATH + '/' + SCHEMA_HELM_TEMPLATE

        appname = self._flux_manifest['appName'].replace(" ", "-")
        namespace = self._flux_manifest['namespace']
        name = self._flux_chart[0]['name']

        # generate Common files
        try:
            with open(common_template, 'r') as f:
                common_schema = f.read()
        except IOError:
            print('File %s not found' % common_template)
            return False
        common_file = plugin_dir + '/' + appname + '/common/constants.py'
        output = common_schema.format(appname=appname, name=name, namespace=namespace)
        
        with open(common_file, "w") as f:
            f.write(output)

        init_file = plugin_dir + '/' + appname + '/common/__init__.py'
        open(init_file, 'w').close()

        chart = self._flux_chart
       
        # Generate Helm files
        try:
            with open(helm_template, 'r') as f:
                helm_schema = f.read()
        except IOError:
            print('File %s not found' % helm_template)
            return False
        
        for idx in range(len(chart)):
            a_chart = chart[idx]

            helm_file = plugin_dir + '/' + appname + '/helm/' + a_chart['name'] + '.py'
            
            name = re.sub(r'[^a-zA-Z0-9 ]', '', a_chart['name'])
            namespace = a_chart['namespace']

            output = helm_schema.format(appname=appname, name=name)

            with open(helm_file, "w") as f:
                f.write(output)
        
        init_file = plugin_dir + '/' + appname + '/helm/__init__.py'
        open(init_file, 'w').close()


        # Generate setup.py
        setupPy_file = plugin_dir + '/setup.py'
        file = """import setuptools\n\nsetuptools.setup(\n    setup_requires=['pbr>=2.0.0'],\n    pbr=True)"""
        
        with open(setupPy_file, 'w') as f:
            f.write(file)

        # Generate setup.cfg file
        setupCfg_file = plugin_dir + '/setup.cfg'


        init_file = plugin_dir + '/__init__.py'
        open(init_file, 'w').close()

        return True

    
    def _create_flux_dir(self, output_dir):

        self._flux_manifest['outputChartDir'] = output_dir + '/charts/'
        self._flux_manifest['outputFluxDir'] = output_dir + '/fluxcd-manifests/'
        self._flux_manifest['outputFluxBaseDir'] = output_dir + '/fluxcd-manifests/base/'

        if not os.path.exists(self._flux_manifest['outputChartDir']):
            os.makedirs(self._flux_manifest['outputChartDir'])
        if not os.path.exists(self._flux_manifest['outputFluxDir']):
            os.makedirs(self._flux_manifest['outputFluxBaseDir'])
            for idx in range(len(self._flux_chart)):
                chart = self._flux_chart[idx]
                self._flux_manifest['outputFluxManifestDir'] = output_dir + '/fluxcd-manifests/' + chart['name']
                os.makedirs(self._flux_manifest['outputFluxManifestDir'])

    
    def _create_plugins_dir(self, output_dir):
        
        self._flux_manifest['outputPluginDir'] = output_dir + '/plugins'
        self._flux_manifest['outputHelmDir'] = output_dir + '/plugins/' + self._flux_manifest['appName'].replace(" ", "-") + '/helm/'
        self._flux_manifest['outputCommonDir'] = output_dir + '/plugins/' + self._flux_manifest['appName'].replace(" ", "-") + '/common/'

        if not os.path.exists(self._flux_manifest['outputPluginDir']):
            os.makedirs(self._flux_manifest['outputPluginDir'])
        if not os.path.exists(self._flux_manifest['outputHelmDir']):
            os.makedirs(self._flux_manifest['outputHelmDir'])
        if not os.path.exists(self._flux_manifest['outputCommonDir']):
            os.makedirs(self._flux_manifest['outputCommonDir'])


    def gen_app(self, output_dir, overwrite):

        self._flux_manifest['outputDir'] = output_dir

        if not os.path.exists(self._flux_manifest['outputDir']):
            os.makedirs(self._flux_manifest['outputDir'])
        elif overwrite:
            shutil.rmtree(self._flux_manifest['outputDir'])
        else:
            print('Output folder %s exists, please remove it or use --overwrite.' % self._flux_manifest['outputDir'])
            return ret

        self._create_flux_dir(output_dir)
        self._create_plugins_dir(output_dir)
        
        ret = self._gen_fluxcd_manifest()
        if ret:
            print('FluxCD manifest generated!')
        else:
            print('FluxCCD manifest generation failed!')
            return ret


        ret = self._gen_plugins()
        if ret:
            print('Plugins generated!')
        else:
            print('Plugins generation failed!')
            return ret


def parse_yaml(yaml_in):
    yaml_data=''
    try:
        with open(yaml_in) as f:
            yaml_data = yaml.safe_load(f)
    except IOError:
        print('Error: %s no found' % yaml_in )
    except Exception as e:
        print('Error: Invalid yaml file')
    return yaml_data


def generate_app(file_in, out_folder, overwrite):
    global TEMP_APP_DIR
    app_data = parse_yaml(file_in)
    if not app_data:
        print('Parse yaml error')
        return
    flux_manifest = FluxApplication(app_data)
    app_out = out_folder + '/' + flux_manifest.get_app_name()
    flux_manifest.gen_app(app_out, overwrite)


def main(argv):
    input_file = ''
    output_folder = '.'
    overwrite = False
    try:
        options, args = getopt.getopt(argv, 'hi:o:', \
                ['help', 'input==', 'output==', 'overwrite'])
    except getopt.GetoptError:
        sys.exit()
    for option, value in options:
        if option in ('-h', '--help'):
            print('StarlingX User Application Generator')
            print('')
            print('Usage:')
            print('    python app-gen.py [Option]')
            print('')
            print('Options:')
            print('    -i, --input yaml_file    generate app from yaml_file')
            print('    -o, --output folder      generate app to output folder')
            print('        --overwrite          overwrite the output dir')
            print('    -h, --help               this help')
        if option in ('--overwrite'):
            overwrite = True
        if option in ('-i', '--input'):
            input_file = value
        if option in ('-o', '--output'):
            output_folder = value

    if not os.path.isfile(os.path.abspath(input_file)):
        print('Error: input file not found')
        sys.exit()
    if input_file:
        generate_app(os.path.abspath(input_file), os.path.abspath(output_folder), overwrite)


if __name__ == '__main__':
    main(sys.argv[1:])