using System;
using System.IO;
using System.Windows.Media.Imaging;
using Autodesk.Revit.UI;


namespace HimFoster
{
    public class App : IExternalApplication
    {
        public Result OnStartup(UIControlledApplication application)
        {
            // Code exécuté quand Revit démarre

            RibbonPanel ribbonPanel = application.CreateRibbonPanel("Him Foster");

            //Creation du boutton
            string thisAssemblyPath = System.Reflection.Assembly.GetExecutingAssembly().Location;
            PushButtonData buttonData = new PushButtonData(
                "HimFosterApp",
                "Him Foster",
                thisAssemblyPath,
                "HimFoster.Command");
            

            PushButton? pushButton = ribbonPanel.AddItem(buttonData) as PushButton;
            if (pushButton !=null)
            {
                //icon

                string imagePath = @"C:\Users\DELL\Documents\BIM\HimFoster\HimFoster\HimFoster.jpg";

                if (File.Exists(imagePath))
                {
                    using (FileStream stream = new FileStream(imagePath, FileMode.Open, FileAccess.Read))
                    {
                        BitmapImage largeImage = new BitmapImage();
                        largeImage.BeginInit();
                        largeImage.StreamSource = stream;
                        largeImage.CacheOption = BitmapCacheOption.OnLoad;
                        largeImage.EndInit();

                        //Image sur le boutton
                        pushButton.LargeImage = largeImage;
                        pushButton.Image = largeImage;
                    }

                }
                else
                {
                    TaskDialog.Show("Image not found", "The specified image path does not exist: " + imagePath, TaskDialogCommonButtons.Ok);
                }

            }

           
                return Result.Succeeded;
        }

        public Result OnShutdown(UIControlledApplication application)
        {
            // Code exécuté quand Revit se ferme
            return Result.Succeeded;
        }
    }
}
