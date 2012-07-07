weibo
=====

weibo => users, statuses, comments, reposts...
  1. Get weibo users detail information, throuth crawler and API;
     parser.py, parser_controller.py, weibo_bilaterals.py, weibo_user_detail.py
	 Currently, we are using weibo_users.py to fetch users' info through api directly.
  2. Get statuses by a certain user or a bunch of users;
     weibo_content.py (write resuts into db) || weibo_content_csv.py (write results into csv files)
  3. Get comments and reposts by a certain status;
     weibo_comm_repo.py

TODO: 
  1. "" // To improve searching efficiency; (using api, get rid of searching temporarily)
  2. "" // Done
  3. To be implemented and tested; 
