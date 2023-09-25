# StarlingX Application Generation Tool

The purpose of this tool is to generate a StarlingX App from a workload/app
in an easy way without the complete StarlingX build environment.

## Why deploy an application as a StarlingX application?

It's important to understand that any user workload can be deployed in many
ways to the Kubernetes cluster(s) that StarlingX manages:

- with the most common Kubernetes package manager, [Helm](https://helm.sh/);
- with [Flux](https://fluxcd.io/), to enjoy all the benefits that come with it
; and finally
- as a StarlingX Application, which benefits from tight integration with the
  [StarlingX system](https://opendev.org/starlingx/config).

## Pre-requisite

- Helm version 2+
- Python version 3.8+
- `pyyaml` version 6.0+
  - `$ pip3 install pyyaml==6.0.1`

## General Overview

![app flowchart](/.etc/app-gen-tool.jpeg)

## 3 Steps to create a Starlingx App

### 1. Prepare Helm chart(s)

#### What is Helm and a Helm chart?

Helm is a Kubernetes package and operations manager. A Helm chart can contain
any number of Kubernetes objects, all of which are deployed as part of the
chart.

The official place to find available Helm Charts is: https://artifacthub.io/.

#### How to develop a Helm chart?

Refer to official [helm doc](https://helm.sh/docs/)

### 2. Create an app manifest

A few essential fields are needed to create the app. The simplest
example is:

```yaml
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

#### 3. Run the StarlingX App Generator

```shell
python3 app-gen.py -i app_manifest.yaml [-o ./output] [--overwrite] [--no-package]|[--package-only]
```

Where:

- `-i/--input`: path to the `app_manifest.yaml` configuration file.
- `-o/--output`: output folder. Defaults to a new folder with the app name in
  the current directory.
- `--overwrite`: deletes existing output folder before starting.
- `--no-package`: only creates the FluxCD manifest, plugins and the
  metadata file, without compressing them in a tarball.
- `--package-only`: create the plugins wheels, sha256 file, helm-chart tarball
  and package the entire application into a tarball.

## Detailed instructions

TODO: add the AppGenGuide from https://github.com/bmuniz-daitan/poc-starlingx-messages
when ready.