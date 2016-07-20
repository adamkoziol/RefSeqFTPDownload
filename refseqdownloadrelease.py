#!/usr/bin/env python
import subprocess
import pycurl
from cStringIO import StringIO
from SPAdesPipeline.OLCspades.accessoryFunctions import *

__author__ = 'adamkoziol'


class FTPdownload(object):

    def release(self):
        printtime('Finding NCBI refseq release number.', self.starttime)
        # Find the release number
        releaseftp = self.baseftp + 'RELEASE_NUMBER'
        body = self.ftpquery(releaseftp)
        # Populate the release number
        self.releasenumber = body.getvalue().rstrip()
        # Make the directory
        self.downloadpath = os.path.join(self.path, 'refseq', self.releasenumber)
        make_path(self.downloadpath)

    def ftplinks(self):
        # Iterate through the categories to download
        for category in self.categories:
            categorymetadata = MetadataObject()
            categorymetadata.name = category
            categorymetadata.ftp = os.path.join(self.baseftp, category) + '/'
            # Initialise a dictionary to store the FTP file names and sizes
            categorymetadata.ftpfiles = dict()
            body = self.ftpquery(categorymetadata.ftp)
            # Split string into a list on newlines
            basicftplist = body.getvalue().split('\n')
            # Find the entries in the list with 'genomic.fna.gz'
            for data in basicftplist:
                if 'genomic.fna.gz' in data:
                    splitdata = data.split()
                    # Store file names and paths in the object
                    categorymetadata.filename = splitdata[8].rstrip('.gz')
                    categorymetadata.categorydownloadpath = os.path.join(self.downloadpath, category)
                    # Create the folder to store the downloads for each category
                    make_path(categorymetadata.categorydownloadpath)
                    # Set the full name/path
                    filepath = os.path.join(categorymetadata.categorydownloadpath, categorymetadata.filename)
                    categorymetadata.ftpfiles[categorymetadata.ftp + splitdata[8]] = {filepath: int(splitdata[4])}
            # Add the metadata to the list of all metadata
            self.organisms.append(categorymetadata)

    def downloading(self):
        from threading import Thread
        # Create the object
        printtime('Downloading files', self.starttime)
        # Start four threads
        for i in range(self.threads):
            # Send the threads to
            threads = Thread(target=self.download, args=())
            # Set the daemon to True - something to do with thread management
            threads.setDaemon(True)
            # Start the threading
            threads.start()
        # Perform the download for each category
        for category in self.organisms:
            # Extract the ftp from the dictionary containing ftp link, full filename, and filesize
            for ftp, pathsize in category.ftpfiles.items():
                # Create nicer looking variables for the values in the dictionary
                path = pathsize.items()[0][0]
                size = pathsize.items()[0][1]
                # Add the necessary variables to the queue
                self.queue.put((category, ftp, path, size))
        self.queue.join()

    def download(self):
        import zlib
        from time import sleep
        while True:
            # Counts downloaded size
            count = 0
            downloading = True
            success = False
            while not success and downloading:
                try:
                    # Get the organism object from the queue
                    category, ftp, filename, size = self.queue.get()
                    # If the file is present, determine the filesize
                    if os.path.isfile(filename):
                        count = os.path.getsize(filename)
                    # If the local filesize is the same as the filesize on the ftp, then don't download
                    if count >= size:
                        # Already downloaded
                        downloading = False
                        success = True
                    else:
                        # Create a StringIO instance to store the file data as it downloads
                        filebuffer = StringIO()
                        # Open the destination file to write
                        with open(filename, 'wb') as localfile:
                            # Create a pycurl instance to download the file
                            curlinstance = pycurl.Curl()
                            # Set the desired encoding type to be gzip
                            curlinstance.setopt(curlinstance.ENCODING, 'gzip')
                            curlinstance.setopt(curlinstance.URL, ftp)
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

    @staticmethod
    def ftpquery(ftpurl):
        """
        Perform FTP queries using pycurl with a supplied FTP link
        :param ftpurl: FTP link to use
        :return: Body information
        """
        # Create a StringIO instance to store data from the curl request
        body = StringIO()
        # Create a pycurl object to determine the size of the file to download
        curlcheck = pycurl.Curl()
        # Use the .setopt attribute to set options
        # The ftp link
        curlcheck.setopt(curlcheck.URL, ftpurl)
        # Write the response to the StringIO instance
        curlcheck.setopt(curlcheck.WRITEFUNCTION, body.write)
        # Run the curl command
        curlcheck.perform()
        # Close
        curlcheck.close()
        # Return the requested data
        return body

    def __init__(self, args, startingtime):
        """
        :param args: list of arguments passed to the script
        Initialises the variables required for this class
        """
        from Queue import Queue
        # Define variables from the arguments - there may be a more streamlined way to do this
        self.args = args
        self.path = os.path.join(args.path, '')
        self.downloadpath = ''
        # Define the start time
        self.starttime = startingtime
        # Use the argument for the number of threads to use
        self.threads = args.threads
        # Assertions to ensure that the provided variables are valid
        make_path(self.path)
        assert os.path.isdir(self.path), u'Supplied path location is not a valid directory {0!r:s}'.format(self.path)
        # Create a list to store the metadata
        self.organisms = list()
        # Create a list of the categories of organisms
        self.categories = ['archaea', 'bacteria', 'fungi', 'invertebrate', 'plant', 'plasmid', 'protozoa',
                           'vertebrate_mammalian', 'vertebrate_other', 'viral']
        # Set the custom categories to use (if necessary)
        if args.category:
            # Create a list from the comma-separated string
            suppliedcategories = args.category.split(',')
            for category in suppliedcategories:
                # if category not in self.categories:
                assert category in self.categories, \
                    '{} is not an acceptable category. Please supply one or more (comma-separated) selections from: {}'\
                    .format(category, ','.join(self.categories))
            self.categories = suppliedcategories
        # The refseq release number - used to separate releases into separate folders
        self.releasenumber = 0
        # Set the URL to be used in FTP queries
        self.baseftp = 'ftp://ftp.ncbi.nlm.nih.gov/refseq/release/'
        # Query the NCBI ftp for the most up-to-date release number
        self.release()
        # Capture the links for the files to download
        self.ftplinks()
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
    parser = ArgumentParser(description='Download genomes from refseq release')
    parser.add_argument('-v', '--version',
                        action='version', version='%(prog)s commit {}'.format(commit))
    parser.add_argument('path',
                        help='Specify path')
    parser.add_argument('-t', '--threads',
                        default=4,
                        help='Number of threads. Default is 4, as I don\'t want to anger NCBI. '
                             'Increase at your own risk')
    parser.add_argument('-c', '--category',
                        help='Choose one or more of the following categories of refseq genomes to download: archaea, '
                             'bacteria, fungi, invertebrate, plant, plasmid, protozoa, vertebrate_mammalian, '
                             'vertebrate_other, viral. Multiple selections should be separated by a comma. '
                             'The script defaults to using all categories.')
    # Get the arguments into an object
    arguments = parser.parse_args()
    starttime = time()
    # Run the pipeline
    FTPdownload(arguments, starttime)
    printtime('Download complete', starttime)
