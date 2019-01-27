# generic profile

This profile configures snakemake to run on any cluster system. The mapping between snakemake ressources and cluster submission can be configured in the cluster_spec.yaml.
In addition, default values are used for all rules not having the snakemake ressource paremeters.

The units are minutes and GB but can be changed.


## Deploy profile

To deploy this profile,
```bash
    mkdir -p ~/.config/snakemake
    cd ~/.config/snakemake
    cookiecutter https://github.com/iromeo/generic.git
```

Configure options, e.g:
```bash
profile_name [myprofile]: generic_qsub
cluster_system [pbs]:
default_queue [debug]:
default_mem_GB [10]: 4
default_threads [8]: 4
default_time_min [300]: 30
```

Then, you can run Snakemake with

    snakemake --profile adaptable_profile ...

so that jobs are submitted to the cluster.
If a job fails, you will find the "external jobid" in the Snakemake error message.
You can investigate the job via this ID.
