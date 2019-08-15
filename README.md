# Enhanced Generic Profile

This profile configures Snakemake to run on any cluster system. This is improved version of generic profile (https://github.com/Snakemake-Profiles/generic) with enhanced cluster profile syntax.

Supported cluster management systems:
* PBS
* LSF
* SLURM (not tested)

Profile was tested and adopted to our PBS and LSF clusters.

## Installation

During installation you will create a cluster configuration profile. This profile describes how your Snakemake job will be submitted to cluster and which params are required for submission. You could install several profiles with different settings.
 
To install this profile,
```bash
    mkdir -p ~/.config/snakemake
    cd ~/.config/snakemake
    cookiecutter https://github.com/iromeo/generic.git
```

Configure default options, e.g:
```bash
profile_name [myprofile]: generic_qsub
cluster_system [pbs]:
default_job_group []:
default_queue []:
default_docker []:
default_email []:
default_mem_GB [10]: 4
default_threads [8]: 4
default_time_min [300]: 30
```

Leave empty values if you don't need this option (e.g. job queue or group) or if option will be always overridden by rule resources section. 

In some cases your LSF or PBS settings could differ from this defaults so it is ok to customize cluster config after installation. 

* Copy config file from `~/.config/snakemake/[your_profile]/cluster_spec.yaml` to your project or modify it in place
* Configure job submission options in `command_options` section, remove options which you don't need, add some missing arguments

# Usage:

* Run Snakemake with option `snakemake --profile your_profile`. 
* If you'd like to use custom `cluster_spec.yaml` please additionally specify option `--cluster-config /path/to/your/custom/cluster_spec.yaml` 

If a job fails, you will find the "external jobid" in the Snakemake error message.
You can investigate the job via this ID.

## Default Options 

Use empty value if option not needed
* `cluster_system`: `pbs`, `lsf` or `slurm`
* `default_job_group`: Specify job group name (used only by LSF in this config)
* `default_queue`: Job Queue
* `default_docker`: Docker container name for LSF submission if needed, e.g. "ubuntu:latest"
* `default_email`: Default email for LSF job status notifications
* `default_time_min`: Default execution time limit in minutes
* `default_mem_GB`: Default memory limit in GB
* `default_threads`: Default job threads/processors number

## Cluster Profile Syntax

* Job management system is specified by property `__default__:system`. If you want to use your own system (e.g. `new`) please add to `~/.config/snakemake/[your_profile]` folder files `new_status.py` which requests job status by job id. Optionally you will need to customize regexp for jobid parsing in the end of `scheduler.py` file.

* `__default__:rule_params_options` options configures which options of rule `params` section could be used by cluster config in `__default__:command_options:[system]:key_mapping` section 

* `__default__:command_options` describes submission script and options for each supported Job management system

* `__default__:command_options:[system]:command` command used for job submission
* `__default__:command_options:[system]:key_mapping` this section describes submission options in form `key:string`.
  * `key` means nothing, it is just for the further convenience.
  * `string` could refer to other properties using `{property_name}`. E.g. `" -n {threads}"` will inline threads value defined `__default__` section or will take it from rule resources section. If `string` contain property reference with empty string value or undefined property, it will be considered as invalid and won't be added to submission command line. You will get warnings about invalid properties in a Snakemake log file
  
  All valid `key_mapping` options will be joined to a commandline in same order.  
 
* Also you could add sections with rule names and customize there some specific options. (not tested)
   E.g. 

    ```yaml
    run_assembler:
      queue: bigmem
      time: 1710
      # threads and memory defined in config file
    ```
