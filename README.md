# liste_blanche_backend

Project that consists in the development of an anti-spam application which is divided in
three parts:

* [Frontend](https://github.com/agustinzorzano/listeBlancheFrontend)
* [API](https://github.com/agustinzorzano/whitelistRest)
* [Backend scripts](https://github.com/agustinzorzano/liste_blanche_backend) 

In this repository we have defined the backend scripts using Python. This scripts allow us 
to connect to a mailbox, analyse it and take the correct actions depending on the user
configuration. In the email analysis, the possible actions that may occur are: 

* The preservation of the email (if the sender is in the whitelist)
* The deletion of the email (if the sender is in the blacklist)
* The transfer of the email into quarantine (if the sender is unknown)

The project was developed during an academic exchange in France in the University "IMT Atlantique"
and it was used as a final academic work in the University "Universidad de Buenos Aires". 


### Setup Virtual Environment
```terminal
python3 -m venv venv
source venv/bin/activate
```

### Store Requirements
```terminal
pip freeze > requirements.txt
```

### Install Requirements
```terminal
pip install -r requirements.txt
```

### Set Up Database
Enter to mysql as a root user and run the following command
```terminal
create database <database_name>;
create user '<username>'@localhost identified by '<password>';
grant all privileges on <database_name>.* to '<username>'@localhost;
flush privileges;
show grants for <username>@localhost;
```
After that we will use this user

### Set Up the environment variables

Define the following environment variables in a .env file

```text
BASE_PATH=<the base path of the emails folder where the quarantine emails are going to be stored>
EMAIL_USER=<email used to send the summary emails>
EMAIL_PASSWORD=<password of the email account>
DATABASE_URL=mysql+pymysql://<database user>:<password>@localhost:3306/<database name>
FRONTEND_ADDRESS=<The frontend address. Example: http://localhost:4200/>
ENCRYPTOR_PUBLIC_KEY_PATH=<The path of the public key>
ENCRYPTOR_PRIVATE_KEY_PATH=<The path of the private key>
```

### Migrate Database
```terminal
flask db init
flask db migrate
flask db upgrade
```

### Run Summary
The user_email must be save in the database
```terminal
python summary.py <user_email>
```

### Run email scan
The user_email must be save in the database
```terminal
python email_scan.py <user_email>
```

### crontab setup
In the crontab we have to define the processes we want to run and when we want to run them. In the crontab we are going to define:
```terminal
# Environment variables
PROJECT_VIRTUAL_ENVIRONMENT_PATH=<path to the activation of the virtual environment. Ex: /home/venv/bin/activate>
PROJECT_USERNAMES_PATH=<path to get_user.py>
PROJECT_EMAIL_SCAN_PATH=<path to email_scan.py>
PROJECT_SUMMARY_PATH=<path to summary.py>
PROJECT_EMAIL_DELETION_PATH=<path to email_deletion.py>

# Processes
0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46,48,50,52,54,56,58 * * * * /bin/bash <path to email_scan.sh> >> <path to a log file> 2>&1

0 0 * * * /bin/bash <path to summary.sh> >> <path to a log file> 2>&1

0 0 * * * /bin/bash <path to email_deletion.sh> >> <path to a log file> 2>&1
```

The first part defines some environment variables which are going to be used in the scripts.
The processes define the time they are going to be executed and
what they are going to execute. The first one is executed each 2 minutes. The other two, are executed everyday at 00:00.


### Run the API with Docker

Build the docker image

`sudo docker build -t project_backend .`

Run the container

`sudo docker run -it -p 5000:5000 --env-file <PATH to the environment file> --mount 'type=bind,src=<PATH to the directory with the private and public keys>,dst=<PATH to the directory with the 2 keys inside the container>' --mount 'type=bind,src=<PATH to the directory where we are going to save the emails>,dst=<PATH to the directory where we are going to save the emails inside the container>' project_backend`

### Application installation

To install the whole application follow the steps defined [here](https://docs.google.com/document/d/1GVVPA1v7WNzyi-QkxMUXnvUEigb7-6ikzjbO08q33EI/edit?usp=sharing) 
