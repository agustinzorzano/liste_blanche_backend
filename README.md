# liste_blanche_backend

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

# Processes
0,5,10,15,20,25,30,35,40,45,50,55 * * * * /bin/bash <path to email_scan.sh> > <path to a log file> 2>&1


0 0 * * * /bin/bash <path to summary.sh> > <path to a log file> 2>&1
```

The first part defines some environment variables which are going to be used in the scripts.
The processes define the time they are going to be executed and
what they are going to execute. The first one is executed each 5 minutes. The second one, is executed everyday at 00:00.


### Run the API with Docker

Build the docker image

`sudo docker build -t project_backend .`

Run the container

`sudo docker run -it -p 5000:5000 --env-file <PATH to the environment file> --mount 'type=bind,src=<PATH to the directory with the private and public keys>,dst=<PATH to the directory with the 2 keys inside the container>' --mount 'type=bind,src=<PATH to the directory where we are going to save the emails>,dst=<PATH to the directory where we are going to save the emails inside the container>' project_backend`

