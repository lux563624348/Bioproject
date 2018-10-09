ssh xli@128.164.54.240 "mkdir -p /home/back_up/Daily_Backup/$(date +%m%d%Y)"
rsync --compress --archive --verbose --exclude={"dev","proc","sys","tmp","run","mnt","media","lost+found","cloud_research"} --hard-links --human-readable --inplace --numeric-ids --delete --link-dest=/home/back_up/201809 -e ssh / xli@128.164.54.240:/home/back_up/Daily_Backup/$(date +%m%d%Y) > /home/crontab_log/Tang.daily.backup_$(date +%m%d%Y_%H.%M).log
