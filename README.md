# Atlassian Statistics (a.k.a. "atstats")
### Purpose:
Pull useful information from the Atlassian APIs and store the results in a [MySQL](https://www.mysql.com/) database for easy querying.  Bonus points for using [QueryTree](https://querytreeapp.com/) to visualize.

### Running:
First of all, you need to [install Docker](https://www.docker.com/products/docker-desktop).  The database and QueryTree visualization tool use docker-compose.  The scraper script runs inside of it's own Docker container.

### Database and QueryTree:
Open a terminal, navigate to the project directory and run `docker-compose up -d`.  This will download the latest MySql and QueryTree images (based on `docker-compose.yml`) and run them as a daemon.
The database is accessible on IP 127.0.0.1 and port 3306.  Check `docker-compose.yml` for credentials.  To shutdown the project, run `docker-compose down`.

QueryTree is accessible at http://localhost:8888/ .  Credentials are `mr_admin@mailinator.com` / `N0tVerySecure!` .

**NOTE:** Due to security concerns, you may need to re-establish the database connection in QueryTree during setup on a new machine.

### The Scraper Script:
You need to build the container the first time or whenever you update the config file:
- `docker build -t atstats_script .`
Run the script to pull data from the APIs and to insert it into the database:
- `docker run --network=atlassian-stats_net atstats_script`

*Beware the network proxies.  There be dragons.*

Custom script parameters can be set in the `Dockerfile` file.