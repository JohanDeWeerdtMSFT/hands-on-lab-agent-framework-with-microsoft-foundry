resource "azurerm_role_assignment" "user_cognitive_services_open_ai_contributor" {
  scope                = azapi_resource.foundry.id
  role_definition_name = "Cognitive Services OpenAI Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_role_assignment" "user_azure_ai_user" {
  scope              = azapi_resource.foundry.id
  role_definition_id = "/subscriptions/${data.azurerm_client_config.current.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/53ca6127-db72-4b80-b1b0-d745d6d5456d"
  principal_id       = data.azurerm_client_config.current.object_id
}

resource "azurerm_role_assignment" "user_azure_ai_project_manager" {
  scope              = azapi_resource.foundry.id
  role_definition_id = "/subscriptions/${data.azurerm_client_config.current.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/eadc314b-1a2d-4efa-be10-5d325db5065e"
  principal_id       = data.azurerm_client_config.current.object_id
}
