#!/usr/bin/env python
import subprocess
from SPAdesPipeline.OLCspades.accessoryFunctions import *

__author__ = 'adamkoziol'


class FTPdownload(object):

    def summaryload(self):
        printtime('Loading summary file.', self.starttime)
        from csv import DictReader
        # Open the summary file as a dictionary
        summary = DictReader(open(self.summaryfile), dialect='excel-tab')
        # Iterate through each row (organism) in the dictionary to create objects
        for organism in summary:
            # Create an object for storing nested static variables
            strainmetadata = MetadataObject()
            # Set the sample name in the object
            strainmetadata.accession = organism['assembly_accession']
            # Iterate through the keys (column headers)
            for column in organism:
                # Add the attributes to the object
                setattr(strainmetadata, column, organism[column]) if column else setattr(strainmetadata, column, 'NA')
            self.organisms.append(strainmetadata)

    def downloading(self):
        from threading import Thread
        printtime('Downloading files', self.starttime)
        # Create and start the threads
        for i in range(self.threads):
            # Send the threads to
            threads = Thread(target=self.download, args=())
            # Set the daemon to True - something to do with thread management
            threads.setDaemon(True)
            # Start the threading
            threads.start()
        for organism in self.organisms:
            # The FTP path takes you to the index of the genomes of the organism. The file I want is in the
            # following format: ftp path + everything after the final '/' + _genomic.fna.gz
            # ftp://ftp.ncbi.nlm.nih.gov/genomes/all/GCF_000002315.4_Gallus_gallus-5.0/GCF_000002315.4_
            # Gallus_gallus-5.0_genomic.fna.gz
            organism.ftp = '{}/{}_genomic.fna.gz'.format(organism.ftp_path, organism.ftp_path.split('/')[-1])
            # Set the names of the compressed and decompressed files
            organism.name = organism.organism_name.replace(' ', '_')
            organism.decompressed = '{}/{}_{}.fa'.format(self.downloadpath, organism.accession, organism.name)
            organism.localfile = organism.decompressed + '.gz'
            self.queue.put(organism)
        self.queue.join()

    def download(self):
        import zlib
        from cStringIO import StringIO
        import re
        from time import sleep
        import pycurl
        while True:
            # Counts downloaded size
            count = 0
            downloading = True
            success = False
            while not success and downloading:
                try:
                    # Get the organism object from the queue
                    organism = self.queue.get()
                    # Create a StringIO instance to store data from the curl request
                    header = StringIO()
                    # Create a pycurl object to determine the size of the file to download
                    curlcheck = pycurl.Curl()
                    # Use the .setopt attribute to set options
                    # The ftp link
                    curlcheck.setopt(curlcheck.URL, organism.ftp)
                    # Only get the headers - not the body
                    curlcheck.setopt(curlcheck.NOBODY, 1)
                    # Write the response to the StringIO instance
                    curlcheck.setopt(curlcheck.WRITEFUNCTION, header.write)
                    # Run the curl command
                    curlcheck.perform()
                    # Close
                    curlcheck.close()
                    # Pull the filesize from the header information
                    organism.filesize = int(re.findall('Content-Length: (.+)\r\n', header.getvalue())[0])

                    # If either the compressed or decompressed file is present, determine the filesize
                    if os.path.isfile(organism.localfile) or os.path.isfile(organism.decompressed):
                        count = os.path.getsize(organism.localfile) if os.path.isfile(organism.localfile) else \
                            os.path.getsize(organism.decompressed)
                    # If the local file size is the same as the filesize on the ftp, then don't download
                    if count >= organism.filesize:
                        # Already downloaded
                        downloading = False
                        success = True
                    else:
                        # Create a StringIO instance to store the file data as it downloads
                        filebuffer = StringIO()
                        # Open the destination file to write
                        with open(organism.decompressed, 'wb') as localfile:
                            # Create a pycurl instance to download the file
                            curlinstance = pycurl.Curl()
                            # Set the desired encoding type to be gzip
                            curlinstance.setopt(curlinstance.ENCODING, 'gzip')
                            curlinstance.setopt(curlinstance.URL, organism.ftp)
                            # Allow pycurl to follow redirects. This isn't required now, but might be n the future
                            curlinstance.setopt(curlinstance.FOLLOWLOCATION, True)
                            # Write the (gzipped) data to the StringIO instance
                            curlinstance.setopt(curlinstance.WRITEFUNCTION, filebuffer.write)
                            curlinstance.perform()
                            curlinstance.close()
                            # Decompress the data - use zlib to decompress the data in the StingIO instance. The
                            # zlib.MAX_WBITS|16 argument tells zlib that the data is gzipped
                            nextline = zlib.decompress(filebuffer.getvalue(), zlib.MAX_WBITS | 16)
                            # Write the data to the file
                            localfile.write(nextline)
                            # Once finished, set success to True to break the while loop
                            success = True
                            downloading = False
                except IOError, e:
                    print '\nDownload error, retrying in a few seconds: ' + str(e)
                    sleep(5)
            dotter()
            # Finish with the thread
            self.queue.task_done()

    def __init__(self, args, pipelinecommit, startingtime, scriptpath):
        """
        :param args: list of arguments passed to the script
        Initialises the variables required for this class
        """
        from Queue import Queue
        # Define variables from the arguments - there may be a more streamlined way to do this
        self.args = args
        self.path = os.path.join(args.path, '')
        self.downloadpath = os.path.join(args.downloadpath, '') if args.downloadpath else '{}downloads'\
            .format(self.path)
        # Define the start time
        self.starttime = startingtime
        # Use the argument for the number of threads to use
        self.threads = args.threads
        # Assertions to ensure that the provided variables are valid
        make_path(self.path)
        assert os.path.isdir(self.path), u'Supplied path location is not a valid directory {0!r:s}'.format(self.path)
        make_path(self.downloadpath)
        assert os.path.isdir(self.downloadpath), u'Supplied download path location is not a valid directory {0!r:s}'\
            .format(self.downloadpath)
        self.commit = str(pipelinecommit)
        self.homepath = scriptpath
        # Ensure that the summary file exists
        self.summaryfile = '{}/assembly_summary_refseq.txt'.format(self.homepath)
        assert os.path.isfile(self.summaryfile), 'Cannot find the required file: assembly_summary_refseq.txt in {}. ' \
                                                 'This file should be provided as part of the git repository. ' \
                                                 'Please ensure that it has not been accidentally deleted' \
            .format(self.homepath)
        # Create a list to store the metadata
        self.organisms = list()
        # Load the information stored in the assembly_summary_refseq.txt file into a dictionary
        self.summaryload()
        # Perform the multithreaded (up to four at once) download
        self.queue = Queue(maxsize=self.threads)
        self.downloading()

# If the script is called from the command line, then call the argument parser
if __name__ == '__main__':
    from time import time
    import os
    # Get the current commit of the pipeline from git
    # Extract the path of the current script from the full path + file name
    homepath = os.path.split(os.path.abspath(__file__))[0]
    # Find the commit of the script by running a command to change to the directory containing the script and run
    # a git command to return the short version of the commit hash
    commit = subprocess.Popen('cd {} && git tag | tail -n 1'.format(homepath),
                              shell=True, stdout=subprocess.PIPE).communicate()[0].rstrip()
    from argparse import ArgumentParser
    # Parser for arguments
    parser = ArgumentParser(description='Download genomes from refseq')
    parser.add_argument('-v', '--version',
                        action='version', version='%(prog)s commit {}'.format(commit))
    parser.add_argument('path',
                        help='Specify path')
    parser.add_argument('-d', '--downloadpath',
                        help='Path in which to place the downloads. If not supplied, this defaults to your current'
                             'working directory/downloads')
    parser.add_argument('-t', '--threads',
                        default=4,
                        help='Number of threads. Default is 4')
    # Get the arguments into an object
    arguments = parser.parse_args()
    starttime = time()
    # Run the pipeline
    FTPdownload(arguments, commit, starttime, homepath)
    printtime('Download complete', starttime)
