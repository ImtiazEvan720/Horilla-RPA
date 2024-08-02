from django.utils import timezone
from django.apps import apps

def create_operation_log(operation_id):
    try:
        
        Operation = apps.get_model('operations', 'Operation')
        OperationLog = apps.get_model('operations', 'OperationLog')

        operation = Operation.objects.get(id=operation_id)
        OperationLog.objects.create(
            operation=operation,
            performed_by=operation.assigned_to,  # Set this as needed or fetch an employee
            date=timezone.now(),
            notes="Automatically logged operation"
        )
    except Operation.DoesNotExist:
        print(f"Operation with ID {operation_id} does not exist.")
