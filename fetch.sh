#/bin/bash

echo "Start to fetch users ..."

DEFAULT_USER_NUMBER=500

if [ -n "$1" ] 
then 
  echo "You want to do $1 users" 
  echo "Running ... // Please using: 'tail -f fetch.log' to view the dynamic logs "
  ./p_weibo_users_2.py -u $1 -p 200 >> ../logs/fetch.log 2>&1
  echo "Done!"
else 
  echo "You want to do the default number of users: $DEFAULT_USER_NUMBER"
  echo "Running ... // Please using: 'tail -f fetch.log' to view the dynamic logs "
  ./p_weibo_users_2.py -u $DEFAULT_USER_NUMBER  -p 200 >> ../logs/fetch.log 2>&1
  echo "Done!"
fi

