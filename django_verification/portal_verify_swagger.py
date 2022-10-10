from custom_packages.swagger_helper_tools.tools import SwaggerTool

manualParametersDict = dict()
tags = [' '.join(['Portal', 'Common', 'Verify'])]
operationDescriptionsDict = dict()

get_verify_swagger_kwargs = SwaggerTool(manualParametersDict, operationDescriptionsDict, tags).get_swagger_kwargs
