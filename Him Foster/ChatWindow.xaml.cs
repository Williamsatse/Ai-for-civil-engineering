using Autodesk.Revit.DB; // Ajout de cette directive using
using Autodesk.Revit.UI;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text.RegularExpressions;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Animation;
using static System.Net.Mime.MediaTypeNames;



namespace HimFoster

{

    public partial class ChatWindow : Window

    {

        private UIApplication _uiapp;

        private UIDocument _uidoc;

        private Autodesk.Revit.DB.Document _doc;

        private List<ChatMessage> _conversationHistory = new List<ChatMessage>();


        public ChatWindow(UIApplication uiapp)

        {

            InitializeComponent();

            _uiapp = uiapp;

            _uidoc = uiapp.ActiveUIDocument;

            _doc = _uidoc.Document;

        }

        private void AddMessage(string sender, string message, bool isUser)
        {
            Border bubble = new Border
            {
                Background = isUser ? new SolidColorBrush(System.Windows.Media.Color.FromRgb(58, 58, 128))
                                    : new SolidColorBrush(System.Windows.Media.Color.FromRgb(45, 45, 60)),
                CornerRadius = new CornerRadius(12),
                Padding = new Thickness(10),
                Margin = new Thickness(isUser ? 100 : 10, 5, isUser ? 10 : 100, 5),
                HorizontalAlignment = isUser ? HorizontalAlignment.Right : HorizontalAlignment.Left,
                MaxWidth = 500,
                Opacity = 0  // <-- on commence invisible
            };

            TextBlock text = new TextBlock
            {
                Text = message,
                TextWrapping = TextWrapping.Wrap,
                Foreground = Brushes.White,
                FontSize = 14
            };

            bubble.Child = text;
            ChatContainer.Children.Add(bubble);

            // 🎬 Animation de fondu (fade-in)
            DoubleAnimation fadeIn = new DoubleAnimation
            {
                From = 0,
                To = 1,
                Duration = TimeSpan.FromSeconds(0.4),
                EasingFunction = new QuadraticEase { EasingMode = EasingMode.EaseOut }
            };
            bubble.BeginAnimation(UIElement.OpacityProperty, fadeIn);
        }


        private void TitleBar_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ButtonState == MouseButtonState.Pressed)
            {
                DragMove();
            }
        }

        private void UserInput_KeyDown(object sender, System.Windows.Input.KeyEventArgs e)
        {
            if (e.Key == System.Windows.Input.Key.Enter)
            {
                {
                    SendButton_Click(sender, e);
                }
            }
        }




        private async void SendButton_Click(object sender, RoutedEventArgs e)

        {

            string userInput = UserInput.Text;

            // Clear the input box
            UserInput.Text = string.Empty;


            if (!string.IsNullOrEmpty(userInput))

            {

                // Display user's message
                AddMessage("Him Foster",userInput, isUser: true);

                _conversationHistory.Add(new ChatMessage { role = "user", content = userInput });

                try
                {

                    // Call ChatGPT API
                    string response = await ChatGPTService.GetResponse(_conversationHistory);

                    // Add assistant's response to the conversation history
                    _conversationHistory.Add(new ChatMessage { role = "assistant", content = response });

                    // Display ChatGPT's response
                    AddMessage("Assistant", response, isUser: false);


                }
                catch (Exception ex)
                {
                    // Display error message
                    AddMessage("Assistant", $"Sorry, an error occurred: {ex.Message}", false);    
                    Console.WriteLine("Exception: " + ex.ToString());
                }
            }


        }

    }

}