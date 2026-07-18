package com.toolsnap.ui.wizard

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import com.toolsnap.config.ComponentTemplates
import com.toolsnap.core.model.ComponentRole
import com.toolsnap.core.model.PendingComponent
import com.toolsnap.core.model.Tool
import com.toolsnap.core.model.ToolCategory
import com.toolsnap.core.model.ToolStatus

/**
 * Sub-navigation within the component linking flow.
 * Shared across ComponentLinkScreen, QuickAddFlow, and SearchLinkFlow.
 */
internal enum class LinkSubscreen {
    LIST,
    PICK_CATEGORY,
    QUICK_ADD_FORM,
    SEARCH_EXISTING,
    SET_ROLE
}

/**
 * Assembly component linking screen — orchestrator.
 *
 * Routes between list, category picker, quick-add form,
 * search existing, and role/quantity picker sub-views.
 */
@Composable
fun ComponentLinkScreen(
    parentCategoryName: String,
    existingComponents: List<PendingComponent>,
    existingTools: List<Tool>,
    onDone: (List<PendingComponent>) -> Unit,
    onCancel: () -> Unit
) {
    val components = remember {
        mutableStateListOf<PendingComponent>().apply {
            addAll(existingComponents)
        }
    }

    var subscreen by remember { mutableStateOf(LinkSubscreen.LIST) }
    var quickAddCategory by remember { mutableStateOf<ToolCategory?>(null) }
    var quickAddTool by remember { mutableStateOf<Tool?>(null) }
    var searchQuery by remember { mutableStateOf("") }
    var rolePickerTool by remember { mutableStateOf<Tool?>(null) }
    var selectedRole by remember { mutableStateOf(ComponentRole.INSERT) }
    var selectedQuantity by remember { mutableStateOf(1) }

    when (subscreen) {
        LinkSubscreen.LIST -> {
            ComponentListView(
                parentCategoryName = parentCategoryName,
                components = components,
                onRemove = { index -> components.removeAt(index) },
                onQuickAdd = { subscreen = LinkSubscreen.PICK_CATEGORY },
                onSearchExisting = {
                    searchQuery = ""
                    subscreen = LinkSubscreen.SEARCH_EXISTING
                },
                onDone = { onDone(components.toList()) },
                onCancel = onCancel
            )
        }

        LinkSubscreen.PICK_CATEGORY -> {
            QuickAddCategoryPicker(
                onCategorySelected = { cat ->
                    quickAddCategory = cat
                    subscreen = LinkSubscreen.QUICK_ADD_FORM
                },
                onBack = { subscreen = LinkSubscreen.LIST }
            )
        }

        LinkSubscreen.QUICK_ADD_FORM -> {
            val cat = quickAddCategory ?: run {
                subscreen = LinkSubscreen.LIST; return
            }
            ManualEntryScreen(
                formFields = ComponentTemplates.fieldsFor(cat),
                title = "New ${cat.displayName}",
                onSave = { attrs ->
                    val tool = Tool(
                        name = buildToolName(cat, attrs),
                        category = cat,
                        status = ToolStatus.CAPTURED
                    )
                    attrs["manufacturer"]?.let { tool.manufacturer = it }
                    attrs["catalog_number"]?.let { tool.catalogNumber = it }
                    for ((k, v) in attrs) {
                        if (k != "manufacturer" && k != "catalog_number") {
                            tool.attributes[k] = v
                        }
                    }
                    tool.touch()
                    quickAddTool = tool
                    rolePickerTool = tool
                    selectedRole = defaultRoleForCategory(cat)
                    selectedQuantity = 1
                    subscreen = LinkSubscreen.SET_ROLE
                },
                onCancel = {
                    quickAddCategory = null
                    subscreen = LinkSubscreen.PICK_CATEGORY
                }
            )
        }

        LinkSubscreen.SEARCH_EXISTING -> {
            SearchExistingView(
                query = searchQuery,
                onQueryChange = { searchQuery = it },
                tools = existingTools,
                alreadyLinkedIds = components.map { it.tool.toolId }.toSet(),
                onToolSelected = { tool ->
                    rolePickerTool = tool
                    selectedRole = defaultRoleForCategory(tool.category)
                    selectedQuantity = 1
                    subscreen = LinkSubscreen.SET_ROLE
                },
                onBack = { subscreen = LinkSubscreen.LIST }
            )
        }

        LinkSubscreen.SET_ROLE -> {
            val tool = rolePickerTool ?: run {
                subscreen = LinkSubscreen.LIST; return
            }
            RoleQuantityPicker(
                toolSummary = tool.displaySummary(),
                toolCategory = tool.category,
                selectedRole = selectedRole,
                selectedQuantity = selectedQuantity,
                onRoleChange = { selectedRole = it },
                onQuantityChange = { selectedQuantity = it },
                onConfirm = {
                    components.add(
                        PendingComponent(
                            tool = tool,
                            role = selectedRole,
                            quantity = selectedQuantity
                        )
                    )
                    quickAddCategory = null
                    quickAddTool = null
                    rolePickerTool = null
                    subscreen = LinkSubscreen.LIST
                },
                onBack = {
                    rolePickerTool = null
                    subscreen = if (quickAddTool != null) {
                        LinkSubscreen.QUICK_ADD_FORM
                    } else {
                        LinkSubscreen.SEARCH_EXISTING
                    }
                }
            )
        }
    }
}
