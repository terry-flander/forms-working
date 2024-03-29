Forms Working
===============================
The Forms Working Development Environment provides a unified platform which enables the **form.io** Forms Designer with a complete Python Flask based website and provides:

- Separate Forms and Data Tenency for multiple applications and data
- User defined Views of application data
- Unlimited number of Forms and Resources supported
- Full role based user security of tenents, views and form submissions
- Managed support for local development and promtes shared environments -- testing, stageing, production, etc.

SERVER ENVIRONMENT

A single AWS EC2 instance can support the application, however if the DB needs to be managed separately, it is best to use either a service (Atlas or AWS) or a separate EC2 instance if self-managed. The production configuration included presumes the DB is in a separate instance.

Forms Working uses Docker to support instances of:
- nginx -- secure front-end webserver
- form.io -- API
- MongoDB -- if installed in the same EC2 instance

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

**FORM.IO** INSTALLATION

from https://github.com/formio/formio/archive/refs/heads/master.zip

1. Get formio-master code fromn GitHub
   ```
   wget https://github.com/formio/formio/archive/refs/heads/master.zip
   ```
2. Unzip downloaded master.zip
   ```
   unzip master
   ```
3. Install git for pulling forms-working repo
   ```
   sudo yum install git
   ``` 
4. Git clone forms-working repo
   ```
   git clone https://github.com/terry-flander/forms-working.git
   ```
5. Install Virtual Environment and Python Libraries
   ```
   python3 -m pip install --user virtualenv
   python3 -m venv env
   source env/bin/activate --system-site-packages
   pip3 install -r requirements.txt
   ```
6. Install node libraries required
   ```
   npm install
   ```
7. Start forms-working
   ```
   mkdir tmp
   ./start [ production | staging | test ]
   ```
Note that the ``start`` script executes the following command which can be used to stop or restart just the Flask webserver with ``./server stop`` and  ``./server restart production`` respectively.

NB: The ``production`` argument above is used by the configuration to use the correct configuration. Leaving this blank results in ``local`` configuration will only work locally, i.e. not in the EC2 instance.

The server log file is ``tmp/webserver.log`` and the application log files is ``tmp/app_info.log``

LOCAL HOST INSTALLATION

The application can be installed on a local host much more easily as there is no need for nginx. You will need Docker and Node/npm however.

1. Install Docker for your OS
2. Install NodeJS and npm for your OS - lots of help on-line
3. Follow the FORM.IO INSTALLATION instructions above but do not start Application
4. Load app forms and data from Production repo with ``./clone_app``
5. Start the application with ``./start``

The Application is running at ``http://localhost:8000/app``
Formio is running at ``http://localhost:3001`` and ``http://localhost:8000``

UNIT TESTING

A suite of testing programs exists using the Python unittest library. All scripts exist in the ``tests`` directory and are executed sequentially using the ``test_app`` script. There are currently just a few tests included in each with the expectation that this will be extended to increase coverate.

1. Validate the entries in ``config/env/test.env`` are correct for your installation.
2. Run the tests with ``./test_app``

NB: Functional tests are not yet included as they must take into count the Flask server framework.

BACKUP AND RESTORE DATA

Scripts are provided which will backup all the data from your connected database which can then be loaded either into an existing data base (restore to previous state), or a new data base (new installation).

Both backup and restore use the **form.io** APIs to access the data so the selected environmnet must include valid connection paramerters to the source data base and that the data base is running and accessible.

BACKUP

To start the backup process execute ``backup_app [ <env> ]`` from the root directory. The optional ``<env>`` parameter will select the source data base. Default is ``local``. Optionally use any of the configurations defined in ``config/env``.

You will be promoted to select either ``full`` or ``incrental`` backup.

- ``full`` -- Export all submissions from all forms and resoruces.
- ``incremental`` -- Export only those submissions which have been changed since the last ``full`` backup. 

 Backup will export either all or changed submissions (records) from each form and resource (table), each into its own named folder with one JSON file for each submission. The resulting directory structure will be zipped into a single file with the name including the type and date of the backup, E.g.:

 - ``backups/full_20220906_1018.zip``
 - ``backups/incremental_20220906_1103.zip``

The date and time of the backup is stored in the separate control file ``backups/version.conf``. If this file does not exist then it is assumed that the backup will be a ``full`` backup.

RESTORE

To start the restore process execute ``restore_app [ <env> ]`` from the root directory. The optional ``<env>`` parameter will select the target data base. Default is ``local``. Optionally use any of the configurations defined in ``config/env``.

You will be presented with a list of all the zip files in ``backups/*``. Select the number corresponding to the backup file to be restored.

**IMPORTANT NOTE**

Passwords on user accounts are not part of the backup and cannot be restored. Since all users must have a password, all are set to 'CHANGEME'. Once logged in the user can change their password using the menu option to initiate the change.