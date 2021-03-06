import sys
from chef import *
from server_helper import *


class chef_helper:

    def __init__(self, chef_config=None):
        if chef_config:
            self.chef = ChefAPI.from_config_file(chef_config)
        else:
            self.chef = autoconfigure()

    def __repr__(self):
        """ Print out current instance of chef_api"""
        outl = 'class :'+self.__class__.__name__

        for attr in self.__dict__:
            outl += '\n\t'+attr+' : '+str(getattr(self, attr))

        return outl

    def build_compute(self, compute_node, environment, user, password):
        '''
        @summary: Builds a controller node
        @param controller_node: The node to build as a controller
        @type controller_node: String
        @param user: user name on controller node
        @type user: String
        @param password: password for the user
        @type password: String
        '''
        # Set node attributes
        chef_node = Node(compute_node, api=self.chef)

        chef_node['in_use'] = "compute"
        chef_node.run_list = ["role[single-compute]"]
        chef_node.save()

        # Set the environment
        self.set_node_environment(chef_node, environment)

        # Run chef client twice
        print "Running chef-client on compute node: %s, \
               this may take some time..." % compute_node
        run1 = self.run_chef_client(chef_node, user, password)
        if run1['success']:
            print "First chef-client run successful, starting second run..."
            run2 = self.run_chef_client(chef_node, user, password)
            if run2['success']:
                print "Second chef-client run successful..."
            else:
                print "Error running chef-client for compute %s" % compute_node
                print run2
                sys.exit(1)
        else:
            print "Error running chef-client for compute %s" % compute_node
            print run1
            sys.exit(1)

    def build_controller(self, controller_node, environment, user, password, ha_num=0, neutron=False):
        '''
        @summary: Builds a controller node
        @param controller_node: The node to build as a controller
        @type controller_node: String
        @param ha_num: If not 0, enabled ha
        @type ha_num: integer
        @param user: user name on controller node
        @type user: String
        @param password: password for the user
        @type password: String
        '''

        chef_node = Node(controller_node, api=self.chef)
        chef_node['in_use'] = "controller"
        if not ha_num == 0:
            print "Making {0} the ha-controller{1} node".format(controller_node, ha_num)
            if neutron:
                chef_node.run_list = ["role[ha-controller{0}]".format(ha_num), "role[single-network-node]"]
            else:
                chef_node.run_list = ["role[ha-controller{0}]".format(ha_num)]
        else:
            print "Making {0} the controller node".format(controller_node)
            if neutron:
                chef_node.run_list = ["role[single-controller]", "role[single-network-node]"]
            else:
                chef_node.run_list = ["role[single-controller]"]
        chef_node.save()

        # Set the environment
        self.set_node_environment(chef_node, environment)

        # Run chef-client twice
        print "Running chef-client for controller node, this may take some time..."
        run1 = self.run_chef_client(chef_node, user, password)
        if run1['success']:
            print "First chef-client run successful, starting second run..."
            run2 = self.run_chef_client(chef_node, user, password)
            if run2['success']:
                print "Second chef-client run successful..."
            else:
                print "Error running chef-client for controller %s" % controller_node
                print run2
                sys.exit(1)
        else:
            print "Error running chef-client for controller %s" % controller_node
            print run1
            sys.exit(1)

    def build_quantum(self, quantum_node, environment, user, password):
        '''
        @summary Builds a Quantum Network Node
        @param quantum_node: The node to build as a controller
        @type quantum_node: String
        @param ha_num: If not 0, enabled ha
        @type ha_num: integer
        @param user: user name on controller node
        @type user: String
        @param password: password for the user
        @type password: String
        '''

        # Gather node info
        chef_node = Node(quantum_node, api=self.chef)
        print "Making {0} the quantum network node".format(quantum_node)
        chef_node['in_use'] = 'quantum'
        chef_node.run_list = ["role[single-network-node]"]
        chef_node.save()

        # Set the environment
        self.set_node_environment(chef_node, environment)

        # Run chef-client twice
        print "Running chef-client for controller node, this may take some time..."
        run1 = self.run_chef_client(chef_node, user, password)
        if run1['success']:
            print "First chef-client run successful, starting second run..."
            run2 = self.run_chef_client(chef_node, user, password)
            if run2['success']:
                print "Second chef-client run successful..."
            else:
                print "Error running chef-client for controller %s" % quantum_node
                print run2
                sys.exit(1)
        else:
            print "Error running chef-client for controller %s" % quantum_node
            print run1
            sys.exit(1)

    def build_swift(self, swift_node, swift_role, environment, user, password):
        '''
        @summary Builds a Swift Node
        @param swift_node: The node to build as a controller
        @type swift_node: String
        @param swift_role: The Role that the node will have
        @type swift_role: String
        @param environment: The environemnt of the node
        @param environment: String
        @param user: user name on controller node
        @type user: String
        @param password: password for the user
        @type password: String
        '''
        # Set node role
        chef_node = Node(swift_node, api=self.chef)
        chef_node['in_use'] = '{0}'.format(swift_role)
        chef_node.run_list = ['role[{0}]'.format(swift_role)]
        chef_node.save()

        # Set the environment
        self.set_node_environment(chef_node, environment)

        # Run chef-client twice
        print "Running chef-client for controller node, this may take some time..."
        run1 = self.run_chef_client(chef_node, user, password)
        if run1['success']:
            print "First chef-client run successful, starting second run..."
            run2 = self.run_chef_client(chef_node, user, password)
            if run2['success']:
                print "Second chef-client run successful..."
            else:
                print "Error running chef-client for controller %s" % quantum_node
                print run2
                sys.exit(1)
        else:
            print "Error running chef-client for controller %s" % quantum_node
            print run1
            sys.exit(1)

    def print_nodes(self):
        # prints all the nodes in the chef server
        for node in Node.list(api=self.chef):
            print node

    def print_environments(self):
        for env in Environments.list(api=self.chef):
            print env

    def set_node_environment(self, node, environment):
        print "Setting node %s chef_environment to %s" % (str(node), environment)
        node.chef_environment = environment
        node.save()

    def run_chef_client(self, node, user, password):
        '''
        @summary: Builds a controller node
        @param node: The node to run chef-client on
        @type node: String
        @param user: user name on controller node
        @type user: String
        @param password: password for the user
        @type password: String
        '''
        ip = node['ipaddress']
        return run_remote_ssh_cmd(ip, user, password, 'chef-client')
