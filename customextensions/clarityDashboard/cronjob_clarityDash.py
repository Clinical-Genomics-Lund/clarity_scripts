from crontab import CronTab
cron = CronTab(user=True)
cron.remove_all()
#job = cron.new(command='/usr/local/bin/python2.7 /opt/gls/clarity/customextensions/clarityDashboard/ex1.py')
#job = cron.new(comment='clarityDash_job' , command='/usr/local/bin/python2.7 /opt/gls/clarity/customextensions/clarityDashboard/extract_data_clarity_dashboard.py -b https://mtapp046.lund.skane.se -u apiuser -p LateDollarsState592  > /opt/gls/clarity/customextensions/clarityDashboard/ex.log 2>&1') 
#job.hour.on(21)
#job.minute.on(0)

#cron.write()

for job in cron:
    print job
