import os
import os.path
import subprocess
import logging

import distutils
import distutils.core
import distutils.command

logging.basicConfig(format = '%(message)s')
log = logging.getLogger()
log.setLevel(logging.INFO)

version = '1.0.1c'
subject_name = "openssl-%(version)s" % locals()
tarball_fname = '%(subject_name)s.tar.gz' % locals()
tarball_url = 'http://www.openssl.org/source/%(tarball_fname)s' % locals()


def call(*args):
    log.info('Executing: %r', args)
    subprocess.call(args)

start_dir = os.path.dirname(os.path.abspath(__file__))


class basic_command(distutils.core.Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass


class download(basic_command):
    user_options = []

    def run(self):
        # Download and unpack tarball if necessary. NOTE: there is NO validation here!
        if not os.path.isdir(subject_name):
            if not os.path.isfile(tarball_fname):
                call('curl', tarball_url, '--output', tarball_fname)

            call('tar', '-xzf', tarball_fname, subject_name)


class configure(basic_command):
    sub_commands = ['download']
    user_options = []

    def run(self):
        self.run_command('download')
        # Configure
        os.chdir(subject_name)
        call("perl", 'Configure', 'VC-WIN32')
        os.chdir(start_dir)


class patch(basic_command):
    user_options = []

    def run(self):
        self.run_command('configure')
        # Patch one of the build scripts to make sure it'll work with nmake
        os.chdir(subject_name)
        os.chdir('util')
        call('patch', '-f', 'mk1mf.pl', os.path.join(start_dir, "mk1mf_chomp_newlines.patch"))
        os.chdir(start_dir)


class build_ext(basic_command):
    user_options = []

    def run(self):
        self.run_command('patch')
        os.chdir(subject_name)
        call('ms\\do_nasm.bat')
        call('nmake', '-f', 'ms\\ntdll.mak')
        os.chdir(start_dir)


class install_headers(basic_command):
    user_options = []

    def run(self):
        self.run_command('build_ext')
        os.chdir(subject_name)
        includes_dir = os.path.expandvars('$VIRTUAL_ENV/PC/.')
        if not os.path.isdir(includes_dir):
            os.makedirs(includes_dir)
        call('cp', '-R', 'include/*', includes_dir)
        os.chdir(start_dir)


class install_lib(basic_command):
    user_options = []

    def run(self):
        self.run_command('build_ext')
        os.chdir(subject_name)
        lib_dir = os.path.expandvars('$VIRTUAL_ENV/PCBuild/.')
        if not os.path.isdir(lib_dir):
            os.makedirs(lib_dir)
        call('cp', '-R', 'out32dll/*', lib_dir)
        os.chdir(start_dir)


class install(basic_command):
    user_options = []

    def run(self):
        self.run_command('install_headers')
        self.run_command('install_lib')


if __name__ == '__main__':

    distutils.core.setup(
        name = 'OpenSSL',
        version = version,
        cmdclass = dict((x, globals()[x]) for x in
            ('install',
             'install_lib',
             'install_headers',
             'build_ext',
             'patch',
             'configure',
             'download'))
    )
    os.chdir(start_dir)
