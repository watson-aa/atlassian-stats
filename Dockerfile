FROM python:3
ADD . /atstats
WORKDIR /atstats
RUN python3 -m pip install -r requirements.txt

CMD python3 -W ignore get_data.py --start "2019-05-01" --jiraini "config/jira.ini" --bbini "config/bitbucket.ini"