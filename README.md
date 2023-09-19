# StarlingX Application Generation Tool

The purpose of this tool is to generate StarlingX user applications in an easy
way without stx build environment and FluxCD manifest schema knowledge.

## Pre-requisite

1. Helm2 installed
2. python3.8
3. pyyaml = 6.0.1 package

`$ pip3 install pyyaml==6.0.1`

## 3 Steps to create a starlingx user app

#### 1. Prepare a helm chart(s)

##### What is helm and helm chart?

Helm is a Kubernetes package and operations manager. A Helm chart can contain
any number of Kubernetes objects, all of which are deployed as part of the
chart.

A list of official Helm Charts locates [here](https://github.com/helm/charts)

##### How to develop a helm chart?

Refer to official [helm doc](https://helm.sh/docs/)

#### 2. Create an app manifest

A few essential fields needed to create the app, simplest one could be:

```
appManifestFile-config:
  appName: stx-app
  appVersion: 1.0.1
  namespace: default
  chart:
    - name: chart1
      version: 1.0.1
      path: /path/to/chart1
      chartGroup: chartgroup1
  chartGroup:
    - name: chartgroup1
      chart_names:
        - chart1

setupFile-config:
  metadata: 
      author: John Doe
      author-email: john.doe@email.com
      url: johndoe.com
      classifier: # required
        - "Operating System :: OS Independent"
        - "License :: OSI Approved :: MIT License"
        - "Programming Language :: Python :: 3"
```
For more details, please refer to app_manifest.yaml

#### 3. Run app-gen-new.py

`$ python3 app-gen.py -i app_manifest.yaml [-o ./output] [--overwrite] [--no-package] [--package-only]`

* ``-i/--input`` Input app_manifest.yaml file
* ``-o/--output`` Output folder, if none is passed the generator will create a folder 
  with the app name in the current directory.
* ``--overwrite`` Delete existing folder with the same name as the app name
* ``--no-package`` Only creates the fluxcd manifest, the plugins and the
  metadata file
* ``--package-only`` Create the plugins wheels, sha256 file, helm-chart tarball 
  and package the entire application into a tarball.
