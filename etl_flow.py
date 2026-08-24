from prefect import flow
from prefect.schedules import Cron

from main import main


@flow(name="job-data-etl")
def etl_flow():
    main()


if __name__ == "__main__":
    etl_flow.serve(
        name="job-data-etl-daily",
        schedules=[
            Cron(
                "0 9 * * *",
                timezone="Asia/Shanghai",
            )
        ],
    )
