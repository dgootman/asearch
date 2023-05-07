import { useCollection } from "@cloudscape-design/collection-hooks";
import {
  AppLayout,
  Box,
  Container,
  ContentLayout,
  Header,
  Input,
  Link,
  SpaceBetween,
  Table,
  TableProps,
  TextFilter,
  TopNavigation,
} from "@cloudscape-design/components";
import React, { FormEvent, ReactNode, useState } from "react";

class AmazonResult {
  // Raw data
  asin: string;
  description: string;
  img: string;
  price: string;
  rating: number;
  number_of_reviews: number;

  // Derived data
  price_value: number;
}

export const App = () => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [resultsLoading, setResultsLoading] = useState(false);

  const search = () => {
    if (query) {
      const params = new URLSearchParams({
        q: query,
      });

      const fetchResults = async () => {
        const searchResponse = await fetch("/api/search?" + params.toString());
        const searchResults = (await searchResponse.json()) as AmazonResult[];
        searchResults.forEach((result) => {
          result.price_value = result.price
            ? parseFloat(result.price.replace("$", ""))
            : null;
        });
        setResults(searchResults);
      };

      setResults([]);
      setResultsLoading(true);
      fetchResults().finally(() => setResultsLoading(false));
    }
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    search();
  };

  const columnDefinitions: TableProps<AmazonResult>["columnDefinitions"] = [
    {
      id: "img",
      header: <></>,
      cell: (row) => (
        <img src={row.img} style={{ maxWidth: 64, maxHeight: 64 }} />
      ),
    },
    {
      id: "item",
      header: "Item",
      cell: (row) => (
        <Link href={`https://amazon.ca/dp/${row.asin}`}>{row.description}</Link>
      ),
      sortingField: "description",
    },
    {
      id: "price",
      header: "Price",
      cell: (row) => row.price,
      sortingField: "price_value",
    },
    {
      id: "rating",
      header: "Rating",
      cell: (row) => row.rating,
      sortingField: "rating",
    },
    {
      id: "number_of_reviews",
      header: "Number of Reviews",
      cell: (row) => row.number_of_reviews,
      sortingField: "number_of_reviews",
    },
  ];

  const {
    items,
    actions,
    filteredItemsCount,
    collectionProps,
    filterProps,
    paginationProps,
  } = useCollection(results, {
    filtering: {},
    sorting: { defaultState: { sortingColumn: columnDefinitions[1] } },
  });

  return (
    <AppLayout
      navigationHide
      toolsHide
      content={
        <ContentLayout
          header={<Header variant="h1">ASearch: A better Amazon search</Header>}
        >
          <SpaceBetween size="m">
            <Container>
              <Input
                placeholder="Search..."
                value={query}
                onChange={(event) => setQuery(event.detail.value)}
                onKeyDown={({ detail }) => {
                  if (detail.key == "Enter") search();
                }}
              />
            </Container>
            <Table
              {...collectionProps}
              columnDefinitions={columnDefinitions}
              items={items}
              wrapLines
              loading={resultsLoading}
              filter={
                <TextFilter
                  {...filterProps}
                  filteringPlaceholder="Filter"
                  countText={`${filteredItemsCount} ${
                    filteredItemsCount === 1 ? "match" : "matches"
                  }`}
                />
              }
            />
          </SpaceBetween>
        </ContentLayout>
      }
    />
  );
};
