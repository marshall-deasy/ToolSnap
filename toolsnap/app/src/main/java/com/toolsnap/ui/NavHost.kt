package com.toolsnap.ui

import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.LocalContext
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.toolsnap.ui.detail.FieldEditNavHost
import com.toolsnap.ui.detail.SessionDetailScreen
import com.toolsnap.ui.home.HomeScreen
import com.toolsnap.ui.tools.CoatingRecommendationScreen
import com.toolsnap.ui.wizard.WizardNavHost

object Routes {
    const val HOME = "home"
    const val WIZARD = "wizard"
    const val DETAIL = "detail/{folderName}"
    const val EDIT_FIELD = "edit_field/{folderName}/{fieldIndex}"
    const val COATING_GUIDE = "coating_guide"

    fun detail(folderName: String) = "detail/$folderName"
    fun editField(folderName: String, fieldIndex: Int) =
        "edit_field/$folderName/$fieldIndex"
}

@Composable
fun ToolSnapNavHost() {
    val navController = rememberNavController()
    val context = LocalContext.current

    NavHost(navController = navController, startDestination = Routes.HOME) {

        composable(Routes.HOME) {
            HomeScreen(
                onNewSession = {
                    navController.navigate(Routes.WIZARD)
                },
                onSessionClick = { folderName ->
                    navController.navigate(Routes.detail(folderName))
                },
                onCoatingGuide = {
                    navController.navigate(Routes.COATING_GUIDE)
                },
                onExit = {
                    (context as? android.app.Activity)?.finish()
                }
            )
        }

        composable(Routes.WIZARD) {
            WizardNavHost(
                onFinished = {
                    navController.popBackStack(Routes.HOME, inclusive = false)
                },
                onCancelled = {
                    navController.popBackStack(Routes.HOME, inclusive = false)
                }
            )
        }

        composable(Routes.DETAIL) { backStackEntry ->
            val folderName = backStackEntry.arguments
                ?.getString("folderName") ?: ""
            SessionDetailScreen(
                folderName = folderName,
                onBack = { navController.popBackStack() },
                onEditField = { folder, fieldIndex ->
                    navController.navigate(
                        Routes.editField(folder, fieldIndex)
                    )
                }
            )
        }

        composable(Routes.EDIT_FIELD) { backStackEntry ->
            val folderName = backStackEntry.arguments
                ?.getString("folderName") ?: ""
            val fieldIndex = backStackEntry.arguments
                ?.getString("fieldIndex")?.toIntOrNull() ?: 0
            FieldEditNavHost(
                folderName = folderName,
                fieldIndex = fieldIndex,
                onDone = { navController.popBackStack() },
                onCancelled = { navController.popBackStack() }
            )
        }

        composable(Routes.COATING_GUIDE) {
            CoatingRecommendationScreen(
                onBack = { navController.popBackStack() }
            )
        }
    }
}
