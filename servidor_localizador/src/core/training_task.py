from celery import shared_task

@shared_task
def execute_training(training_id: int):
    from src.web.services.nn_service import NNService
    
    service = NNService()
    service.training_nn(training_id)