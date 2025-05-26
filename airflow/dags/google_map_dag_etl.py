import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator


# Définition des arguments par défaut
default_args = {
    'owner': 'master_m2si',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}



# Définition du DAG Airflow
with DAG(
    'Google_map',  # Garder le DAG avec le même nom
    default_args=default_args,
    description='Extraction & Insertion of Google Maps Reviews into PostgreSQL',
    start_date=datetime(2025, 3, 13),
    schedule_interval=None,
    catchup=False
) as dag:

    # Tâche 1 : Extraction des données et sauvegarde JSON
    scraping_task = PythonOperator(
        task_id='extract_data_task',
        python_callable=lambda: __import__('main_scraping_script').main(),
        dag=dag
    )

    # Tâche 2 : Insertion des données et sauvegarde en PostgreSQL 
    insertion_task = PythonOperator(
        task_id='insert_data_task',
        python_callable=lambda: __import__('insert_data').main(),
        dag=dag

    )

    # Tâche 3 : Exécution de dbt pour transformer les données
    transform_phase_1_task = BashOperator(
    task_id='transform_phase_1_task',
    bash_command='cd ~/data_warehouse_project && dbt run --profiles-dir ~/.dbt --models cleaned_reviews',
    dag=dag
    )

    # #Tache 4 : transformation phase 2 
    transform_phase_2_task = PythonOperator(
    task_id='transform_phase_2_task',
    python_callable=lambda: __import__('transform_phase_2').main(),
    dag=dag

    )

    

    #Tache 5 : Design and Load Data into the Data mart 
    load_phase_task=BashOperator(
    task_id='load_phase_task',
    bash_command='cd ~/data_warehouse_project && dbt run --profiles-dir ~/.dbt --profile decisionnelle_profile --models dim_bank dim_branch dim_location dim_sentiment fact_reviews',
    dag=dag
    )

    
    # scraping_task >> insertion_task
     
    scraping_task >> insertion_task >> transform_phase_1_task >> transform_phase_2_task >> load_phase_task
