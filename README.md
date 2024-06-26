# README

This project is designed to fetch and analyze data from top-ranked corporates using a Dockerized application. The analysis results and fetched data are stored in the data folder.

* The script initially scrapes data from the top 25 enterprises and startups displayed on the homepage, then collects and stores details about these corporations in a JSON file named `top_ranked_corporates.json`.

* Next, the script uses Celery to concurrently crawl all listed enterprises, saving their details into a JSON file named `all_corporates.json`.

* After the crawl jobs are completed, the script initiates an analysis task that clusters the corporate data into 10 groups based on their descriptions using the K-means algorithm. The optimal number of clusters, \( k=10 \), is determined using the elbow method.

* Subsequently, the script extracts key phrases from the descriptions of each corporate cluster. It then submits these clusters to Google GEMINI, which generates a descriptive summary and assigns a title for each cluster.

* Finally, the script saves the results to two JSON files: "cluster_descriptions.json" for the cluster summaries and titles, and "corporates_with_clusters.json" for the corporates saved by their respective clusters.


Clone the repository from GitHub using:
```
git clone https://github.com/derya72815/entrapeer.git
cd entrapeer
```

## Configuration

Before running the project, you need to configure the GEMINI API key. This key can be obtained from Google AI.

Open the config.py file.
Replace the placeholder with your GEMINI API key

## Running the Project

**Step 1: Build and Start Docker Containers**

To build and start the Docker containers, run the following command:
```
docker-compose up --build
```
This command will build the Docker images and start the containers. The top-ranked corporates will be fetched and saved in the data folder as the application starts.

**Step 2: Trigger the Main Task**

To trigger the main task, run the following curl command:
```
curl -X POST "http://localhost:8000/trigger-analysis" -H "Content-Type: application/json" -d '{"user_id": "example_user_id"}'
```
This command will:
* Fetch all the corporates.
* Perform the analysis.
* Save the fetched data and analysis results in the data folder.
You can monitor the process in the Docker terminal.

**Step 3: Check Task Status**
While fetching data, you can check the status of the task with the following curl command:
```
curl -X GET "http://localhost:8000/task-status/<task_id>"
```
Replace the task ID with the actual task ID provided by the command line status. This command will return the current status of the task.

* By following the steps outlined above, you can successfully configure, run, and monitor the project. The fetched data and analysis results will be stored in the data folder for further use.

