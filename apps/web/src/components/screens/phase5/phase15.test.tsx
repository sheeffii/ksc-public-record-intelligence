import "@/test/next-mocks";
import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { renderWithProviders } from "@/test/render";
import { DirectoryScreen } from "./DirectoryScreen";
import { DocumentReaderScreen, SearchScreen } from "./ReaderSearchScreens";
import { RealPersonScreen, RealWitnessScreen } from "./RealRecordScreens";

const counts = {
  documentMentions: 1,
  transcriptMentions: 0,
  exhibitRefs: 0,
  findings: 0,
  witnessesWhoReferred: 0,
  incidents: 0,
  citationsResolved: 0,
};

describe("Phase 15 real-data production surfaces", () => {
  it("renders an honest empty directory without demo records or flags", () => {
    renderWithProviders(<DirectoryScreen kind="people" screenTitle="People" initialRows={[]} />);
    expect(screen.getByText(/No verified people/i)).toBeInTheDocument();
    expect(document.querySelector("[data-demo-flag]")).not.toBeInTheDocument();
    expect(document.body).not.toHaveTextContent(/Demo record|demo-person|F-DEMO/i);
  });

  it("renders source-backed people and code-only protected witnesses", () => {
    const { unmount } = renderWithProviders(
      <RealPersonScreen
        person={{
          slug: "public-person",
          displayName: "Public Person",
          role: "Public role",
          aliases: [],
          counts,
        }}
      />,
    );
    expect(screen.getAllByText("Public Person").length).toBeGreaterThan(0);
    expect(document.body).not.toHaveTextContent(/demo/i);
    unmount();
    renderWithProviders(
      <RealWitnessScreen
        witness={{ code: "W00001", protected: true, protectiveMeasures: ["pseudonym"] }}
      />,
    );
    expect(screen.getAllByText("W00001").length).toBeGreaterThan(0);
    expect(screen.getByText(/No private identity is inferred/i)).toBeInTheDocument();
  });

  it("renders parsed reader content with exact coordinates and parser state", () => {
    renderWithProviders(
      <DocumentReaderScreen
        id="F00001"
        initialPage={2}
        initialDocument={{
          id: "F00001",
          title: "Public filing",
          type: "decision",
          language: "en",
          page: 2,
          paragraphs: [{ number: 12, page: 2, pdfPageIndex: 1, text: "Exact parsed public text." }],
          citation: {
            sourceType: "court",
            ref: "F00001",
            docId: "F00001",
            resolved: true,
            display: "F00001 · ¶12",
          },
          visibility: "public_redacted",
          pageCount: 3,
          versionRef: "F00001/RED",
          artifactStatus: "fetched",
          parserName: "ksc-native-pdf",
          parserVersion: "2",
          parseRequiresReview: false,
          sourceUrl: "https://www.scp-ks.org/public-record/F00001",
        }}
      />,
    );
    expect(screen.getByText("Exact parsed public text.")).toBeInTheDocument();
    expect(screen.getByText("¶12")).toBeInTheDocument();
    expect(screen.getByText("ksc-native-pdf/2")).toBeInTheDocument();
  });

  it("keeps Court and External search results visibly separate", () => {
    renderWithProviders(
      <SearchScreen
        initialQuery="public"
        sourceScope="both"
        initialResults={[
          {
            id: "F00001",
            category: "documents",
            title: "Court document",
            context: "Court Record",
            href: "/documents/F00001",
          },
          {
            id: "m1",
            category: "external",
            title: "Public report",
            context: "Publisher",
            href: "https://example.org/report",
          },
        ]}
      />,
    );
    expect(screen.getByRole("heading", { name: "Documents" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "External Public Sources" })).toBeInTheDocument();
    expect(screen.getByText("External Public Source")).toBeInTheDocument();
  });
});
