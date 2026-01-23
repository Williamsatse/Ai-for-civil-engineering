using System.Linq.Expressions;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using HimFoster;
using System.Windows.Interop;

// Ajout de l'importation du namespace Autodesk.Revit.UI pour le type Result

namespace HimFoster
{
    [Transaction(TransactionMode.Manual)]
    public class Command : IExternalCommand
    {
        public Autodesk.Revit.UI.Result Execute(
            ExternalCommandData commandData,
            ref string message,
            ElementSet elements)
        {
            try
            {
                // Show the chat window
                ChatWindow chatWindow = new ChatWindow(commandData.Application);
                WindowInteropHelper helper = new WindowInteropHelper(chatWindow);
                helper.Owner = System.Diagnostics.Process.GetCurrentProcess().MainWindowHandle;

                //Affiche la fenetre
                chatWindow.Show();

                return Autodesk.Revit.UI.Result.Succeeded; // <-- Ajout du préfixe de namespace complet

            }
            catch (Exception ex)
            {
                TaskDialog.Show("Error", "Failed to launch Him Foster: " + ex.Message);
                return Result.Failed;
            }
        }
    }
}