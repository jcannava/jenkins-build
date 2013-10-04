"""
OpenStack Features
"""

class Feature(object):
    """ Represents a OpenStack Feature
    """

    def __init__(self, config=None):
        self.config = config
    
    def __repr__(self):
        """ print current instace of class
        """
        outl = 'class :' + self.__class__.__name__
        for attr in self.__dict__:
            outl += '\n\t' + attr + ' : ' + str(getattr(self, attr))
        return outl

    def _pre_configure(self):
        pass

    def _apply_feature(self):
        pass

    def _post_configure(self):
        pass

    @classmethod
    def remove_chef(cls, node):
        """ Removes chef from the given node
        """

        if node.os == "precise":
            commands = ["apt-get remove --purge -y chef",
                        "rm -rf /etc/chef"]
        if node.os in ["centos", "rhel"]:
            commands = ["yum remove -y chef",
                        "rm -rf /etc/chef /var/chef"]

        command = commands.join("; ")

        return node.run_cmd(command, quiet=True)

    @classmethod
    def prepare_cinder(cls, node):
        """ Prepares the node for use with cinder
        """

        # Clean up any VG errors
        commands = ["vg=`pvdisplay | grep unknown -A 1 | grep VG | "
                    "awk '{print $3}'`",
                    "for i in `lvdisplay | grep 'LV Name' | grep $vg "
                    "| awk '{print $3}'`; do lvremove $i; done",
                    "vgreduce $vg --removemissing"]
        command = commands.join("; ")
        node.run_cmd(command)

        # Gather the created volume group for cinder
        command = "vgdisplay 2> /dev/null | grep pool | awk '{print $3}'"
        ret = node.run_cmd(command)
        volume_group = ret['return'].replace("\n", "").replace("\r", "")
        
        # Update our environment
        env = node.environment
        cinder = {
            "storage": {
                "lvm": {
                    "volume_group": volume_group
                }
            }
        }
        env._add_override_attr("cinder", cinder)

    @classmethod
    def run_chef_client(cls, node):
        """ Runs chef-client on the given node
        """

        return node.run_cmd('chef-client', quiet=True)


class ChefServer(Feature):
    """ Represents a chef server
    """

    def __init__(self):
        super(ChefServer, self).__init__()
        self.iscript = self.config['chef']['server']['install_script']
        self.iscript_name = self.iscript.split('/')[-1]
        self.install_commands = ['curl {0} >> {1}'.format(
                                    self.iscript,
                                    self.iscript_name),
                                 'chmod u+x ~/{0}'.format(self.iscript_name),
                                 './{0}'.format(self.iscript_name)
                                ]

    def _pre_configure(self, node):
        self.remove_chef(node)

    def _apply_feature(self, node):
        self._install(node)
    
    def _post_configure(self, node):
        self._install_cookbooks(node)

    def _install(self, node):
        """ Installs chef server on the given node
        """

        command = self.install_commands.join("; ")
        node.run_cmd(command)

    def _install_cookbooks(self, node):
        """ Installs cookbooks on node
        """
        
        cookbook_url = self.config['rcbops'][node.product]['git']['url']
        cookbook_branch = node.branch
        cookbook_name = cookbook_url.split("/")[-1].split(".")[0]
        install_dir = self.config['chef']['server']['install_dir']

        commands = ["mkdir -p {0}".format(install_dir),
                    "cd {0}".format(install_dir),
                    "git clone {0} --recursive".format(cookbook_url),
                    "cd {0}/cookbooks".format(cookbook_url),
                    "git checkout {0}".format(cookbook_branch)]

        if 'cookbooks' in cookbook_name:
             # add submodule stuff to list
            commands.append('cd /opt/rcbops/chef-cookbooks')
            commands.append('git submodule init')
            commands.append('git submodule sync')
            commands.append('git submodule update')
            commands.append('knife cookbook upload --all --cookbook-path'
                            '{0}/{1}/cookbooks'.format(install_dir,
                                                       cookbook_name))
        else:
            commands.append('knife cookbook upload --all'
                            ' --cookbook-path {0}/{1}'.format(install_dir,
                                                              cookbook_name))

        commands.append('knife role from file {0}/{1}/roles/*.rb'.format(
            install_dir, cookbook_name))

        command = commands.join("; ")

        return node.run_cmd(command)

class HighAvailability(Feature):
    """ Represents a highly available cluster
    """

    def __init__(self, number):
        super(HighAvailability, self).__init__()
        self.number = number
        self.environment = self.config['environments']['ha']

    def _pre_configure(self, node):
        self.prepare_cinder(node)

    def _apply_feature(self, node):
        self.run_chef_client(node)


class Neutron(Feature):
    """ Represents a neutron network cluster
    """

    def __init__(self):
        super(Neutron, self).__init__()
        self.environment = self.config['environments']['neutron']

    def pre_configure(self):
        raise NotImplementedError

    def apply_feature(self, node):
        self.run_chef_client(node)
    
    def post_configure(self):
        raise NotImplementedError


class OpenLDAP(Feature):
    """ Represents a keystone with an openldap backend
    """

    def __init__(self):
        super(OpenLDAP, self).__init__()
        self.environment = self.config['environment']['ldap']
        self.ldapadd_cmd = 'ldapadd -x -D "cn=admin,dc=rcb,dc=me -wostackdemo -f /root/base.ldif'

    def pre_configure(self):
        raise NotImplementedError

    def apply_feature(self, node):
        self.run_chef_client(node)
    
    def post_configure(self):
        self._ldap_add()

    def _ldap_add(self):
        raise NotImplementedError


class GlanceCF(Feature):
    """ Represents a glance with cloud files backend
    """

    def __init__(self):
        super(GlanceCF, self).__init__()
        self.environment = self.config['environment']['glance']

    def pre_configure(self):
        raise NotImplementedError

    def apply_feature(self):
        raise NotImplementedError
    
    def post_configure(self):
        raise NotImplementedError


class Swift(Feature):
    """ Represents a block storage cluster enabled by swift
    """

    def __init__(self):
        super(Swift, self).__init__()
        self.environment = self.config['environment']['swift']

    def pre_configure(self):
        raise NotImplementedError

    def apply_feature(self):
        raise NotImplementedError
    
    def post_configure(self):
        raise NotImplementedError