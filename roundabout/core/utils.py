# Import environment variables from .env files
import environ
env = environ.Env()

# Set sitewide variables for headings/labels display
# Uses environmental variables from .env files
# These are then used in context_processors for templates and forms.py for form labels

def set_app_labels():
    # Set pattern variables from .env configuration
    RDB_LABEL_ASSEMBLIES_SINGULAR = env('RDB_LABEL_ASSEMBLIES_SINGULAR', default='Assembly')
    RDB_LABEL_ASSEMBLIES_PLURAL = env('RDB_LABEL_ASSEMBLIES_PLURAL', default='Assemblies')
    RDB_LABEL_BUILDS_SINGULAR = env('RDB_LABEL_BUILDS_SINGULAR', default='Build')
    RDB_LABEL_BUILDS_PLURAL = env('RDB_LABEL_BUILDS_PLURAL', default='Builds')
    RDB_LABEL_DEPLOYMENTS_SINGULAR = env('RDB_LABEL_DEPLOYMENTS_SINGULAR', default='Deployment')
    RDB_LABEL_DEPLOYMENTS_PLURAL = env('RDB_LABEL_DEPLOYMENTS_PLURAL', default='Deployments')
    RDB_LABEL_INVENTORY_SINGULAR = env('RDB_LABEL_INVENTORY_SINGULAR', default='Inventory')
    RDB_LABEL_INVENTORY_PLURAL = env('RDB_LABEL_INVENTORY_PLURAL', default='Inventory')

    labels = {
        # Assemblies
        'label_assemblies_app_singular': RDB_LABEL_ASSEMBLIES_SINGULAR,
        'label_assemblies_app_plural': RDB_LABEL_ASSEMBLIES_PLURAL,
        # Builds
        'label_builds_app_singular': RDB_LABEL_BUILDS_SINGULAR,
        'label_builds_app_plural': RDB_LABEL_BUILDS_PLURAL,
        # Deployments
        'label_deployments_app_singular': RDB_LABEL_DEPLOYMENTS_SINGULAR,
        'label_deployments_app_plural': RDB_LABEL_DEPLOYMENTS_PLURAL,
        # Deployments
        'label_inventory_app_singular': RDB_LABEL_INVENTORY_SINGULAR,
        'label_inventory_app_plural': RDB_LABEL_INVENTORY_PLURAL,
    }

    return labels
