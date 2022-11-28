conda activate base
conda create -y --name check_services
conda activate check_services
conda install -y -c conda-forge python=3.10 git pyyaml psutil
