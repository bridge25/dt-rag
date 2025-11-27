import React from "react"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../tabs"

describe("Tabs", () => {
  const TabsExample = () => (
    <Tabs defaultValue="tab1">
      <TabsList>
        <TabsTrigger value="tab1">Tab 1</TabsTrigger>
        <TabsTrigger value="tab2">Tab 2</TabsTrigger>
        <TabsTrigger value="tab3">Tab 3</TabsTrigger>
      </TabsList>
      <TabsContent value="tab1">
        <p>Content 1</p>
      </TabsContent>
      <TabsContent value="tab2">
        <p>Content 2</p>
      </TabsContent>
      <TabsContent value="tab3">
        <p>Content 3</p>
      </TabsContent>
    </Tabs>
  )

  test("renders all tabs", () => {
    render(<TabsExample />)
    expect(screen.getByText("Tab 1")).toBeInTheDocument()
    expect(screen.getByText("Tab 2")).toBeInTheDocument()
    expect(screen.getByText("Tab 3")).toBeInTheDocument()
  })

  test("shows default tab content", () => {
    render(<TabsExample />)
    expect(screen.getByText("Content 1")).toBeInTheDocument()
    // Content 2 and 3 are hidden
    expect(screen.queryByText("Content 2")).not.toBeInTheDocument()
    expect(screen.queryByText("Content 3")).not.toBeInTheDocument()
  })

  test("switches tab content on click", async () => {
    const user = userEvent.setup()
    render(<TabsExample />)

    const tab2 = screen.getByText("Tab 2")
    await user.click(tab2)

    await waitFor(() => {
      expect(screen.getByText("Content 2")).toBeInTheDocument()
    })
    expect(screen.queryByText("Content 1")).not.toBeInTheDocument()
  })

  test("highlights active tab", async () => {
    const user = userEvent.setup()
    render(<TabsExample />)

    const tab1 = screen.getByText("Tab 1")
    expect(tab1).toHaveAttribute("data-state", "active")
    expect(tab1).toHaveAttribute("aria-selected", "true")

    const tab2 = screen.getByText("Tab 2")
    await user.click(tab2)

    await waitFor(() => {
      expect(tab2).toHaveAttribute("data-state", "active")
      expect(tab2).toHaveAttribute("aria-selected", "true")
    })
    expect(tab1).toHaveAttribute("data-state", "inactive")
    expect(tab1).toHaveAttribute("aria-selected", "false")
  })

  test("has accessible attributes", () => {
    render(<TabsExample />)

    const tab1 = screen.getByText("Tab 1")
    expect(tab1).toHaveAttribute("role", "tab")
    expect(tab1).toHaveAttribute("aria-selected", "true")

    const tab2 = screen.getByText("Tab 2")
    expect(tab2).toHaveAttribute("aria-selected", "false")
  })
})

describe("Tabs with controlled value", () => {
  test("uses controlled value", () => {
    const ControlledTabs = () => {
      const [value, setValue] = React.useState("tab2")

      return (
        <Tabs value={value} onValueChange={setValue}>
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2">Tab 2</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
          <TabsContent value="tab2">Content 2</TabsContent>
        </Tabs>
      )
    }

    render(<ControlledTabs />)
    expect(screen.getByText("Content 2")).toBeInTheDocument()
  })
})
