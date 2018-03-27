# DZbot
DZbot is a project aimed at making certain ops work easier. For example, it allows users to send pager duty incidents
from a hipchat room to a pager duty user  

DZbot can be extended and deployed to any hipchat room as long as the person deploying it is an **admin** of the room.    


## Interface
DZbot is called like any other command line program (`/dzbot list --entity users --name test user`)
```commandline
/dzbot -h
usage: cli.py [-h] {list,override,notify,ensure-oncalls} ...

positional arguments:
  {list,override,notify,ensure-oncalls}
    list                list all specified entities or a single entity
    override            override the current schedule for the specified user
    notify              send an incident to a user or escalation policy
    ensure-oncalls      ensure that each ep has an oncall level 1 and oncall
                        level 2 user

optional arguments:
  -h, --help            show this help message and exit


list each escalation policy, user, oncall, service, or schedule names
command: /dzbot list --entity eps/users/oncalls/services/schedules
return:
['Amp',
'Amp-NonEssential',
'Android',
'AWS CheckMK',
'Content Engineering',
'Data Engineering',
'DataScience',
'DBA',
'Default',
'Ingestion',
'iOS',
'Operations',
'ops-delayed',
'OpsDirect',
'Radioedit',
'Radioedit-delayed',
'Test',
'Web',
'Web Escalation']


list an escalation policy's oncall users & their contact info by their escalation level
command: /dzbot list --entity eps: Operations
return: 
1: ['Test User 1, email: testuser1@iheartmedia.com, phone: 1112223333']
2: ['Test User 2, email: testuser2@iheartmedia.com & testuser2@ihr.com, phone: 2223334444']
3: ['Test User 3, email: testuser3@iheartmedia.com, phone: 3334445555']
4: ['Test User 4, email: testuser4@iheartmedia.com, phone: 4445556666 & 5556667777']


list the specified oncall user's contact info
command: /dzbot list --entity oncalls --name Test User 1
return: 'email': ['testuser1@iheartmedia.com'], 'phone': ['1112223333']


Send an incident to a pagerduty user
command: /dzbot notify --entity users --name Test User 1 --service Test Service --title test  --message this is a test
return: successfully sent users incident to Test User 1


Send an incident to a pagerduty escalation policy
command: /dzbot notify --entity eps --name Test ep --service Test Service --title test --message this is a test
return: successfully sent eps incident to Test ep


list each escalation policy that don't have a primary or secondary oncall level set
command: /dzbot ensure-oncalls
return:
['Amp-NonEssential: oncall level 2 does not exist',
'Android: oncall level 2 does not exist',
'AWS CheckMK: oncall level 2 does not exist',
'Test: oncall level 2 does not exist',
'Web: oncall level 2 does not exist']
``` 

## Zappa 
DZbot uses the open source project ****Zappa**** to automate AWS Lambda deployments and updates.
 
`https://github.com/Miserlou/Zappa/blob/master/README.md`

Run this zappa command in terminal after your code changes/extensions:

`zappa update dev_testuser/zappa update production`


## Add Production DZbot Into a Hipchat Room
You must be the **admin** of a hipchat room to add the DZbot integration.

1. Select 'Integrations' in the hipchat room (under the 3 ellipses sign)
2. Select 'Install new integrations'
3. Scroll to the bottom of the page from the pop up window
4. Select 'Install an integration from a descriptor URL'
5. Paste `https://ixafbupha7.execute-api.us-east-1.amazonaws.com/production/capability-descriptor` into the field
6. Continue & Approve the DZbot addon
7. If the hipchat room is private, then you have to invite @dzbot to join the room
8. Send `/dzbot --help` in the chatroom for a command line interface of options


## Dev Setup 
1. Have Python 3.6 installed 
    - `which python3`
2. Have virtualenv installed 
    - `pip3 install virtualenv` 
3. Have a valid AWS account and make sure your AWS credentials file is properly installed
    - `https://aws.amazon.com/blogs/security/a-new-and-standardized-way-to-manage-credentials-in-the-aws-sdks/`
    - `https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html`
4. Clone the DZbot repo via ssh `git@github.com:iheartradio/dzbot.git`
5. cd into the repo and create a new virtualenv (venv) folder
    - `virtualenv venv`
    - Make sure Python 3.6 is installed in the venv folder
6. Activate the virtual environment
    - `source venv/bin/activate`
7. Install the project dependencies in the virtual environment
    - `python setup.py install`
8. Open `zappa_settings.json` and add a new json object with name `dev_testuser` as follows:
    ```json
    {
      "production": {
        "app_function": "src.dzbot.app.app",
        "aws_region": "us-east-1",
        "profile_name": "default",
        "project_name": "dzbot",
        "runtime": "python3.6",
        "s3_bucket": "zappa-q2y2dlp29"
      },
      "dev_testuser": {
        "app_function": "src.dzbot.app.app",
        "aws_region": "us-east-1",
        "profile_name": "default",
        "project_name": "dzbot",
        "runtime": "python3.6",
        "s3_bucket": "zappa-q2y2dlp29"
      }
    }
    ```  
9. Deploy your new dev stage
    - `zappa deploy dev_testuser`
    - Copy the outputted url from the above command
        - `Deployment complete!: https://k8kba2dbz1.execute-api.us-east-1.amazonaws.com/dev_testuser` 
11. Add Production stage environment variables to your new dev stage
    - Copy vars from `https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions/dzbot-production?tab=graph`
    - Paste vars into your dev lambda `https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions/dzbot-testuser?tab=graph`  
10. Create a  new testroom in hipchat and install your dev dzbot integration with its descriptor URL
    - Follow the `Add DZbot Into a Hipchat Room` steps to integrate dzbot with the testroom
    - The descriptor URL should be the outputted url from above + `capability-descriptor` 
        - `https://7k6anj0k99.execute-api.us-east-1.amazonaws.com/dev_testuser/capability-descriptor`
11. Extend code (follow the `Extend` steps below) and update Lambda to reflect these changes
    - `zappa update dev_testuser`
12. Test your dev dzbot in the testroom to see if it responds properly
13. Submit a pull request for review & update code if necessary 
14. Delete the dev stage after merging your PR 
    - `zappa undeploy dev_testuser` 

    
## Extend
1. Add command line option for new dzbot functionality in `src/dzbot/cli.py`
2. Write extension code in an existing service directory (`src/pager_duty/pd.py`) or add a new service directory
3. Extend `create_outbound_msg` function in `src/dzbot/utils.py`
4. Update your Lambda dev stage to reflect these changes (`zappa update dev_testuser`)
5. Test dzbot in your test room


## Inspect Logs
You can find logs for dzbot in the `/aws/lambda/dzbot-production` Log Group in AWS CloudWatch
1. Sign-in to AWS Console
2. Under `Services` select `CloudWatch`
3. Select `Logs` on the left hand panel and then select the `/aws/lambda/dzbot-production` log group
4. The log stream at the top is the most recent recorded DZbot activity
5. The specific logs detailing what the user sent to DZbot can be found under the `DEBUG` messages


## Monitoring
To extend DZbot's monitoring capabilities, follow these instructions:

`https://github.com/Miserlou/Zappa#scheduling`

General Guideline
1. Create a new monitoring function to be periodically called in `src/dzbot/app.py`
2. Update the `zappa_settings.json` file by adding your new function to `"events"`
3. If you need to remove your monitoring function
    - Delete the extended part of `"events"` that you added to `zappa_settings.json` 
    - Run `zappa unschedule production` 
    - Run `zappa update` 

## Run Tests
Tests follow normal `setup.py` conventions.

Please make sure each new method you write is tested!  

`python setup.py test`

## Coding Standards
Code in the project should follow PEP8 standards, with the exception that lines can be up to 120 characters. The build
will check this for you.

Please also follow:
1. All code that should be tested, is tested. Tests should be included in the same PR as the your change. All tests should be written using pytest.
2. All methods should be documented. It should be clear the parameters expected, and what results a consumer might get.
3. All methods should return values. Avoid manipulation of parameters without explicitly returning the value.
