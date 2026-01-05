import type { Plugin } from "@opencode-ai/plugin"

/**
 * Ring Notification Plugin
 * Desktop notification when sessions complete.
 *
 * Provides desktop notifications for session events,
 * useful when running long-running tasks in the background.
 *
 * Platform support:
 * - macOS: Uses osascript for native notifications
 * - Linux: Uses notify-send if available
 * - Windows: Uses PowerShell toast notifications
 */
export const RingNotification: Plugin = async ({ $ }) => {
  const sendNotification = async (title: string, message: string) => {
    const platform = process.platform

    try {
      if (platform === "darwin") {
        // macOS
        await $`osascript -e ${"display notification \"" + message + "\" with title \"" + title + "\""}`
      } else if (platform === "linux") {
        // Linux with notify-send
        await $`notify-send ${title} ${message}`
      } else if (platform === "win32") {
        // Windows PowerShell toast
        const script = `
          [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
          $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
          $textNodes = $template.GetElementsByTagName("text")
          $textNodes.Item(0).AppendChild($template.CreateTextNode("${title}")) | Out-Null
          $textNodes.Item(1).AppendChild($template.CreateTextNode("${message}")) | Out-Null
          $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
          [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Ring").Show($toast)
        `
        await $`powershell -Command ${script}`
      }
    } catch {
      // Notification not critical - fail silently
    }
  }

  return {
    event: async ({ event }) => {
      if (event.type === "session.idle") {
        await sendNotification("Ring", "Session completed!")
      }

      if (event.type === "session.error") {
        await sendNotification("Ring", "Session encountered an error")
      }
    }
  }
}

export default RingNotification
