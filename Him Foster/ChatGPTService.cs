using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;
using System.Collections.Generic;
using System.Linq;

namespace HimFoster
{
    public static class ChatGPTService
    {
        // ⚠️ Remplace par ton token GitHub personnel
        private static readonly string apiKey = "Api key here";

        public static async Task<string> GetResponse(List<ChatMessage> conversationHistory)
        {
            // Préparer les messages pour la requête
            var messages = conversationHistory.Select(msg => new ChatMessage
            {
                role = msg.role,
                content = msg.content
            }).ToList();

            string systemPrompt = @" You are Him Foster, an integral part of Revit itself—think of yourself as the built-in expert guide woven right into the software, not some external chatbot. You have complete, up-to-date knowledge of every feature, tool, workflow, and best practice in Autodesk Revit, from modeling and documentation to advanced BIM techniques.

              Your mission is to supercharge the user's productivity: provide clear, step-by-step instructions to get tasks done faster, smarter, and with fewer clicks. Offer tips to optimize workflows, avoid common pitfalls, and boost efficiency in design, modeling, and collaboration. Always focus on practical, actionable advice tailored to Revit users.

             When responding:
             - Be precise: For tasks like 'how to create a structural column,' clearly direct to the tool (e.g., 'Go to the Structure tab > Column panel > Structural Column') and explain the steps in a numbered list for quick execution.
             - Keep it friendly and a little quirky—add a dash of fun or personality, like 'Let's build that column like a pro!' to make learning enjoyable, but do not use or send any emojis in your responses.
             - Assume the user is in Revit and guide them as if you're right there in the interface.
             - Always respond in the language in which the user's question is asked, addressing their concerns directly in that language.

              Stay on-topic with Revit; if something's unrelated, gently steer back to how it ties into the software.
               ";

            if (!messages.Any(m => m.role == "system"))
            {
                messages.Insert(0, new ChatMessage
                {
                    role = "system",
                    content = systemPrompt
                });
            }

            const int maxTokens = 3500;
            int currentTokenCount = EstimateTokenCount(messages);

            while (currentTokenCount > maxTokens)
            {
                messages.RemoveAt(1);
                currentTokenCount = EstimateTokenCount(messages);
            }

            using (var client = new HttpClient())
            {
                // 🔗 GitHub Models endpoint
                var endpoint = "https://models.github.ai/inference/v1/chat/completions";

                // 🔑 Ajout du token GitHub
                client.DefaultRequestHeaders.Add("Authorization", $"Bearer {apiKey}");

                // Corps de la requête
                var requestBody = new
                {
                    model = "openai/gpt-4.1-mini",  // ou "openai/gpt-4.1"
                    messages = messages
                };

                var content = new StringContent(
                    JsonConvert.SerializeObject(requestBody),
                    Encoding.UTF8,
                    "application/json"
                );

                try
                {
                    var response = await client.PostAsync(endpoint, content);
                    var responseString = await response.Content.ReadAsStringAsync();

                    if (!response.IsSuccessStatusCode)
                    {
                        Console.WriteLine($"API Error: {response.StatusCode}");
                        Console.WriteLine($"Error Details: {responseString}");
                        throw new Exception($"API call failed with status code {response.StatusCode}");
                    }

                    var responseObject = JsonConvert.DeserializeObject<ChatGPTResponse>(responseString);

                    if (responseObject?.choices == null || responseObject.choices.Count == 0 ||
                        responseObject.choices[0]?.message?.content == null)
                    {
                        throw new Exception("La réponse de l'API est vide ou mal formée.");
                    }

                    return responseObject.choices[0].message.content.Trim();
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Exception occurred: {ex.Message}");
                    throw;
                }
            }
        }

        private static int EstimateTokenCount(List<ChatMessage> messages)
        {
            int tokenCount = 0;
            foreach (var msg in messages)
            {
                tokenCount += msg.content.Length / 4;
            }
            return tokenCount;
        }
    }

    // --- Classes pour la sérialisation / désérialisation ---

    public class ChatGPTResponse
    {
        public List<Choice> choices { get; set; } = new List<Choice>();
    }

    public class Choice
    {
        public ChatMessage? message { get; set; }
    }

    public class ChatMessage
    {
        public required string role { get; set; }
        public required string content { get; set; }
    }
}
