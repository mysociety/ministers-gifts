from pathlib import Path
from typing import Literal, NewType

import httpx
import pandas as pd
from bs4 import BeautifulSoup

URL = NewType("URL", str)


def get_release_urls() -> list[URL]:
    base_url = "https://www.gov.uk/government/collections/register-of-ministers-gifts-and-hospitality"
    index_page = httpx.get(base_url)
    index_soup = BeautifulSoup(index_page.text, "html.parser")

    # get all a links with a class of govuk-link

    links = index_soup.find_all("a", class_="govuk-link")
    link_urls = [link["href"] for link in links]
    # reduce to links that start '/government/publications/register-of-ministers-gifts-and-hospitality'

    link_urls = [
        "https://www.gov.uk" + link
        for link in link_urls
        if link.startswith(
            "/government/publications/register-of-ministers-gifts-and-hospitality"
        )
    ]

    return link_urls


def get_csv_links_from_page(page_url: URL) -> list[URL]:
    page = httpx.get(page_url)
    page_soup = BeautifulSoup(page.text, "html.parser")

    # get all links that are .csvs
    csv_links = page_soup.find_all("a")
    csv_links = [link["href"] for link in csv_links if link["href"].endswith(".csv")]

    lower_links = [link.lower() for link in csv_links]

    # discard links that contains 'csv-preview'
    csv_links = [link for link in csv_links if "csv-preview" not in link.lower()]

    # check that all links contain either 'gifts' or 'hospitality'

    for link in lower_links:
        if "gifts" not in link and "hospitality" not in link:
            raise ValueError(f"Link {link} does not contain 'gifts' or 'hospitality'")

    return csv_links


def get_dept(s: str):
    # get first part seperated by __
    s = s.split("__")[0]
    return s.replace("_", " ").title()


def get_csv(csv_url: URL):
    try:
        df = pd.read_csv(csv_url, encoding="utf-8")
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(csv_url, encoding="latin1")
        except Exception:
            # As a last resort
            df = pd.read_csv(csv_url, encoding="cp1252")

    if "Value (Â£)" in df.columns:
        # rename to Value (£)
        df = df.rename(columns={"Value (Â£)": "Value (£)"})

    if "Estimated value of Hospitality (£)" in df.columns:
        # rename to Value of Hospitality (£)
        df = df.rename(
            columns={"Estimated value of Hospitality (£)": "Value of Hospitality (£)"}
        )

    df.columns = [x.strip() for x in df.columns]
    # drop unnamed columns
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    df["Department"] = get_dept(get_final_part_of_url(csv_url))
    df["source_slug"] = get_final_part_of_url(csv_url)

    # convert Date column from either iso or UK datetime to iso datetime
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True).dt.date

    # "Nil return" values should be "Nil Return" for consistency

    df = df.replace("Nil return", "Nil Return")

    return df


def get_final_part_of_url(s: str):
    s = s.split("/")[-1]
    if s.endswith(".csv"):
        s = s[:-4]
    return s


def get_all_csvs(csv_type: Literal["gifts", "hospitality"]):
    dfs: list[pd.DataFrame] = []
    releases = get_release_urls()
    for r in releases:
        csv_links = [
            link for link in get_csv_links_from_page(r) if csv_type in link.lower()
        ]
        csv_links = sorted(list(set(csv_links)))
        for csv in csv_links:
            df = get_csv(csv)
            df["release_slug"] = get_final_part_of_url(r)
            dfs.append(df)
    return pd.concat(dfs)


def download_and_store():
    gift_df = get_all_csvs("gifts")
    hospitality_df = get_all_csvs("hospitality")

    hospitality_df["Value of Hospitality (£)"] = hospitality_df[
        "Value of Hospitality (£)"
    ].astype(str)

    gift_df["nil_return"] = gift_df["Value (£)"].str.lower() == "nil return"
    hospitality_df["nil_return"] = (
        hospitality_df["Value of Hospitality (£)"].str.lower() == "nil return"
    )

    package_path = Path("data", "packages", "ministers_gifts_and_hospitality")

    gift_df.to_parquet(package_path / "gifts.parquet")
    hospitality_df.to_parquet(package_path / "hospitality.parquet")
