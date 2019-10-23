# Installing emailer in Docker

Using Docker may be helpful to keep the Python environment clean.  Or maybe it's too complicated.  But here's some instructions if you want to try.

## 1. Install Docker on your server.

You can rent a Linux server for about $5 a month at digitalocean.com, or maybe cheaper at Google Cloud Platform or Amazon Web Services.

Ubuntu install instructions here: https://docs.docker.com/install/linux/docker-ce/ubuntu/

## 2. Copy these files over.

Copy the files in this folder into your server, in the "emailer" folder in your home folder (`~/emailer/`).

* `docker-compose.yml` - tells docker how to setup the volumes and build the file
* `Dockerfile` - sets up Python, installs emailer, and runs emailer

## 3. Build the docker container

Run `docker-compose build` from inside the `~/emailer/` folder.

This will download python, and install emailer and it's depenencies into a container.  So it won't mess with your system's python environment.

Docker Compose is being used, because it is good at passing variables to `docker run` like the volume, and naming the container.

## 4. Setup the config file

Run `docker-compose run --rm emailer /bin/sh`
This will put you in a shell in the docker container.

Now run `email --sample-config > emailer.json` to create a config file.
The file will be saved outside the container because the docker-compose file maps the local folder to the folder in the container.

Finally type `exit` to exit the docker container.

Now open the `emailer.json` file and replace the appropriate fields.
Under `keys` there is a `testkey`, each key can be a different Google Sheet schedule so you can run schedules for multiple groups.  For example `"springfield": "ABC"` for a Google sheet who's id is "ABC" that represents Springfield's schedule.

Also open up `Dockerfile` and replace `testkey` with whatever you named the key. (ex. `springfield`)

## 5. Run emailer to make sure it has OAuth access.

We need to run emailer once now to save your login to google.

Run `docker-compose run --rm emailer email -v --test --all-keys`

Copy the OAuth URL, and paste it into the browser, login as the user that will be sending email (Maybe create a new gmail account just for this).  If there was an error about setting up gmail or sheets APIs, then follow the error's instructions and set that up.

## 6. Setup Cron to run this daily.

On the server type `crontab -e`.  This will probably open up your cron in VIM, so here's some specific instructions including saving and exiting vim. :tada:

In the following command, `55 18 * * *` means at minute 55 of the hour 18, or 6:55pm every day.  So change those numbers as you see fit.

* Press the down arrow until you get to the bottom.  Then press 'o' to start a new line.
* Type: `PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`
* Press Enter
* Type: `55 18 * * * cd $HOME/emailer && docker-compose run emailer >> emailer.log 2>&1`
* Then press ESC
* Now type ZZ

Note: The time 6:55pm is based on whatever the system's timezone is.  You can double check this by running `date` and it will say something like "Wed Sep 26 22:53:45 PDT 2018" where "PDT" means the server is set to Pacific Daylight Time timezone.

Any errors will be saved in the `~/emailer/emailer.log` file.  And you can look at the time of the file or `sudo grep cron /var/log/syslog` to see when the command last ran.

Hope that helps!
