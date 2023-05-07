import { useCollection } from "@cloudscape-design/collection-hooks";
import {
  AppLayout,
  Container,
  ContentLayout,
  Grid,
  Header,
  Input,
  Link,
  Select,
  SpaceBetween,
  Table,
  TableProps,
  TextFilter,
} from "@cloudscape-design/components";
import { OptionDefinition } from "@cloudscape-design/components/internal/components/option/interfaces";
import React, { FormEvent, useState } from "react";
import useLocalStorageState from "use-local-storage-state";

class AmazonResult {
  // Raw data
  asin: string;
  description: string;
  link: string;
  img: string;
  price: string;
  rating: number;
  number_of_reviews: number;

  // Derived data
  num: number;
  price_value: number;
}

export const App = () => {
  const [query, setQuery] = useState("");
  const [country, setCountry] = useLocalStorageState("ctry", {
    defaultValue: {
      label: "🇨🇦 Canada",
      value: "CA",
    } as OptionDefinition,
  });
  const [results, setResults] = useState([]);
  const [resultsLoading, setResultsLoading] = useState(false);

  const search = () => {
    if (query) {
      const params = new URLSearchParams({
        q: query,
        ctry: country.value,
      });

      const fetchResults = async () => {
        const searchResponse = await fetch("/api/search?" + params.toString());
        const searchResults = (await searchResponse.json()) as AmazonResult[];
        searchResults.forEach((result, index) => {
          result.num = index + 1;
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
      id: "num",
      header: "#",
      cell: (row) => row.num,
      sortingField: "num",
    },
    {
      id: "item",
      header: "Item",
      cell: (row) => <Link href={row.link}>{row.description}</Link>,
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
          header={<Header variant="h1">ASearch: a better Amazon search</Header>}
        >
          <SpaceBetween size="m">
            <Container>
              <Grid
                gridDefinition={[
                  { colspan: { default: 12, xxs: 8, xs: 9, s: 10 } },
                  { colspan: { default: 12, xxs: 4, xs: 3, s: 2 } },
                ]}
              >
                <Input
                  placeholder="Search..."
                  inputMode="search"
                  type="search"
                  autoComplete
                  autoFocus
                  value={query}
                  onChange={(event) => setQuery(event.detail.value)}
                  onKeyDown={({ detail }) => {
                    if (detail.key == "Enter") search();
                  }}
                />
                <Select
                  selectedOption={country}
                  onChange={({ detail }) => setCountry(detail.selectedOption)}
                  options={[
                    { label: "🇨🇦 Canada", value: "CA" },
                    { label: "🇺🇸 United States", value: "US" },
                  ]}
                />
              </Grid>
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
