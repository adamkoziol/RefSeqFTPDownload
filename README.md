# RefSeqFTPDownload

# Requirements

* Linux

If you plan on running installing the required modules using setup.py, following an `apt-get update` 
the following packages need to be installed:

* git
* build-essential
* python-pip
* python-dev
* zlib1g-dev
* libcurl4-openssl-dev
* libssl-dev

`sudo apt-get install -y build-essential git python-pip python-dev zlib1g-dev libcurl4-openssl-dev libssl-dev`

# Installation

Clone the repository (--recursive will clone the necessary submodules):

`git clone https://github.com/adamkoziol/RefSeqFTPDownload.git --recursive`

Install python dependencies:

	
```
cd RefSeqFTPDownload/
python setup.py install
```

# Usage
## refseq release

Used to download refseq release ( ftp://ftp.ncbi.nlm.nih.gov/refseq/release/ ). By default the script downloads the 
entirety of the release, but it is possible to specify one or more of the following categories to download:

* archaea
* bacteria
* fungi
* invertebrate
* plant
* plasmid
* protozoa
* vertebrate_mammalian
* vertebrate_other
* viral

### Example command

`python refseqdownloadrelease.py -c viral /refseq/downloads`

A path to the folder in which the downloads are to be placed is required. See usage below:

```
usage: refseqdownloadrelease.py [-h] [-v] [-d DOWNLOADPATH] [-t THREADS]
                           [-c CATEGORY]
                           path

Download genomes from refseq release

positional arguments:
  path                  Specify path

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -t THREADS, --threads THREADS
                        Number of threads. Default is 4, as I don't want to
                        anger NCBI. Increase at your own risk
  -c CATEGORY, --category CATEGORY
                        Choose one or more of the following categories of
                        refseq genomes to download: archaea, bacteria, fungi,
                        invertebrate, plant, plasmid, protozoa,
                        vertebrate_mammalian, vertebrate_other, viral.
                        Multiple selections should be separated by a comma.
                        The script defaults to using all categories.
```

## refseq

Uses the supplied assembly_summary_refseq.txt file to determine ftp paths of every organism in refseq, and downloads
each \*_genomic.fna.gz file in the database. If you replace the assembly_summary_refseq.txt file with a new version,
( ftp://ftp.ncbi.nlm.nih.gov/genomes/refseq/assembly_summary_refseq.txt ), please ensure that you delete any comments 
at the top of the file.

### Example command

`python refseqdownload /refseq`

A path to the folder in which the downloads are to be placed is required. See usage below:

```
usage: refseqdownload.py [-h] [-v] [-d DOWNLOADPATH] [-t THREADS] path

Download genomes from refseq

positional arguments:
  path                  Specify path

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -d DOWNLOADPATH, --downloadpath DOWNLOADPATH
                        Path in which to place the downloads. If not supplied,
                        this defaults to your current working directory/downloads
  -t THREADS, --threads THREADS
                        Number of threads. Default is 4
```