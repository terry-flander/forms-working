OPS Portal
===============================
The OPS Portal provides a unified platform for managing Eloque assets information through the following stages:
- Initial Design
- Preliminary mapping of fibers and sensor layouts
- Generation of DIS As-Designed documentation
- Generation of DIS As -Built documentation
- Integration to meta-data repositories including Analytics and Transpara
- Integration to external drafting tools, i.e. AutoCAD

SERVER ENVIRONMENT

The two AWS components required for server installation are:
1. EC2 Instance connected through a load balancer to the FQDNS console.eloque.com
2. MongoDB Atlas managed instance

The ops-oportal application uses Docker to support instances of:
- nginx -- secure front-end webserver
- form.io -- API

INSTALLATION INSTRUCTIONS

Install Docker on Amazon Linix

   from : https://www.cyberciti.biz/faq how-to-install-docker-on-amazon-linux-2/

1. Login into remote AWS server using the ssh command:
   ```
   ssh ec2-user@ec2-ip-address-dns-name-here
   ```
2. Apply pending updates using the yum command:
   ```
   sudo yum update
   ```
3. Search for Docker package:
   ```
   sudo yum search docker
   ```
4. Get version information:
   ```
   sudo yum info docker
   ```
5. Install docker, run:
   ```
   sudo yum install docker
   ```
6. Add group membership for the default ec2-user so you can run all docker commands without using the sudo command:
   ```
   sudo usermod -a -G docker ec2-user
   id ec2-user
   newgrp docker
   ```
7. Install docker-compose
   ```
   sudo pip3 install docker-compose
   ```
8. Enable docker service at AMI boot time:
   ```
   sudo systemctl enable docker.service
   ```
9. Start the Docker service:
   ```
   sudo systemctl start docker.service
   ```
10. Check status
   ```
   sudo systemctl status docker.service
   ```
Install Node and npm
   ```
   sudo yum install -y gcc-c++ make 
   curl -sL https://rpm.nodesource.com/setup_16.x | sudo -E bash - 
   sudo yum install -y nodejs
   ```

Check install with
   ```
   node -v
   npm -v
   ```

FORM.IO INSTALLATION

from https://github.com/formio/formio/archive/refs/heads/master.zip

1. Get formio-master code fromn GitHub
   ```
   wget https://github.com/formio/formio/archive/refs/heads/master.zip
   ```
2. Unzip downloaded master.zip
   ```
   unzip master
   ```
3. Install git for pulling ops-portal repo
   ```
   sudo yum install git
   ```
4. Git clone ops-portal repo
   ```
   git clone https://git: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@github.com/FiBridge/ops-portal.git
   ```
5. Install Python Libraries
   ```
   mkdir env
   pip3 install -t env -r requirements.txt
   ```
6. (PRODUCTION ONLY) Install the ops-portal configuration files into formio-master
   ```
   cp ops-portal/config/* formio-master
   ```
7. Install node libraries required
   ```
   npm install
   docker-compose up
   ```
8. Start ops-portal
   ```
   mkdir tmp
   ./webserver start production
   ```
Note that the start script execuites the following command and can also be used to stop or restart the server with ``./start stop`` and  ``./start restart production`` respectively.

NB: The ``production`` argument above is used by the configuration to use the correct configuration. Leaving this blank results in ``development`` configuration will only work locally, i.e. not in the EC2 instance.

The server log file is ``tmp/webserver.log``
   ```
   nohup python3 -m wsgi &> tmp/webserver.log & echo $! > tmp/http.server.pid &
   ```

LOCAL HOST INSTALLATION

The application can be installed on a local host much more easily as there is no need for nginx. You will need Docker and Node/npm however.

1. Install Docker for your OS
2. Install NodeJS and npm for your OS - lots of help on-line
3. Follow the FORM.IO INSTALLATION instructions above

EXCEPT #6 -- DO NOT COPY ANYTHING INTO THE formio-master directory
AND    #8 -- Database must be loaded  before starting server

4. Load app forms and data from Production repo with ``./clone_app``
5. Start the application with ``./server`` or ``./server start development``

A webserver is running at ``http://localhost:8000/app``
Formio is running at ``http://localhost:3001``

UNIT TESTING

A suite of testing programs exists using the Python unittest library. All scripts exist in the ``tests`` directory and are executed sequentially using the ``test_app`` script. There are currently just a few tests included in each with the expectation that this will be extended to increase coverate.

1. Validate the entries in ``config/env/test.env`` are correct for your installation.
2. Run the tests with ``./test_app``

NB: Functional tests are not yet included as they must take into count the Flask server framework.

