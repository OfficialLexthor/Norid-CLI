# RDAP service – Norid
RDAP is a lookup service for domain data. The letters stand for Registration Data Access Protocol. Norid’s RDAP service is based on the international RDAP protocol.

The service is designed as a REST-API and is therefore well suited for automated lookups.

Access
------

The service is available at:

```
rdap.norid.no
```


The service is in production.

Testing
-------

The test system has it's own RDAP service. This is available at:

```
rdap.test.norid.no
```


Why use RDAP
------------

RDAP is considered to be the successor to the current whois protocol and includes a number of improvements compared to this protocol.

*   The transfer format for lookup data is clearly specified as JSON format, and is easy to process automatically.
*   Character sets are uniquely specified.
*   The protocol offers the option of so-called _layered access_. This means that privileged users can be authenticated and gain access to more data compared to anonymous users. This could include more detailed data or a larger lookup rate.

How the service works
---------------------

The service is available at the following URL:

`rdap.norid.no`

The service supports lookups of domain names, contact data (entities) and name servers. Some examples:

Domain name lookup:  
[https://rdap.norid.no/domain/norid.no](https://rdap.norid.no/domain/norid.no)

Lookup of contact person with personal handle as the key:  
[https://rdap.norid.no/entity/NH55R-NORID](https://rdap.norid.no/entity/NH55R-NORID)

Lookup of registrar with registrar-ID as the key:  
[https://rdap.norid.no/entity/reg1-NORID](https://rdap.norid.no/entity/reg1-NORID)

Lookup of name server with name server handle as the key:  
[https://rdap.norid.no/nameserver\_handle/X11H-NORID](https://rdap.norid.no/nameserver_handle/X11H-NORID)

Search for name server with a certain host name:  
[https://rdap.norid.no/nameservers?name=x.nic.no](https://rdap.norid.no/nameservers?name=x.nic.no)

RDAP is designed as a web service. Queries are submitted as URLs, to which the server responds with data in JSON format. RDAP uses the HTTP method GET to look up data on an object. The HTTP method HEAD is used to submit a query for whether an object exists.

Data lookup
-----------

Data for an object (domain name, contact or name server) can be looked up using the HTTP method GET. This is equivalent to a lookup in the whois protocol. The response to the lookup is the return code 200 OK and a set of JSON data if the object exists, and _404 Not Found_ if it does not.

### Query for whether an object exists

A query for whether an object (domain name, contact or name server) is registered is submitted using the HTTP method HEAD. This is equivalent to a lookup in the DAS protocol. The query returns the return code 200 OK if the object exists, and _404 Not Found_ if it does not

### Query for unavailable domains

Some domains are not available for registration. The negative answer from a HEAD request does not show whether the domain can be registered or not.

To see whether a domain can be registered, a GET request must be used. For a domain that is not registered, a _404 Not Found_ message is returned. Additional information is then provided if it is not available for registration. If the domain is permanently unavailable, the returned message is 'Domain is not available for registration'. If the domain is temporarily unavailable, the message is 'Domain is currently not available for registration'.

Local adjustments
-----------------

The RDAP protocol is an international standard, but it allows local extensions and adjustments.

Norid's RDAP server has some local extensions in addition to the standardized queries. Please note that these extensions do not change the behaviour or return data for any of the other standardized queries.

A general RDAP client should therefore be able to handle standardized queries without any compatibility issues.

### Extension for looking up name servers

The standard lookup for name server objects use name server host names as the lookup key. In Norid’s registration system, name server lookups keyed to host names will not be unique, as the system may contain several name server objects with the same host name. We have therefore chosen to offer a separate lookup for name servers based on name server handles:

[https://rdap.norid.no/nameserver\_handle/X11H-NORID](https://rdap.norid.no/nameserver_handle/X11H-NORID)

These lookups will return a data object formatted the same way as standard RDAP lookups for name servers.

### Lookup for domain count

The following query returns the number of domain names registered on a subscriber, given by identity. The query can be used with organization number and personal-id as key:

[https://rdap.norid.no/norid\_domain\_count/987654321](https://rdap.norid.no/norid_domain_count/987654321)

The query returns the number of domain names registered directly under .no as well as the number of domains registered under any sublevel domains.

Authenticated access
--------------------

Authenticated access gives the client extended data in the query results, and an extended set of query methods. RDAP clients authenticates by using https 'basic authentication' as described in the standard RFC-2617.

### Create an authenticated user

All registrars can authenticate their access to RDAP. As a registrar, you must then do as follows:

*   You must create a user for RDAP. This is done on the [registrarweb](https://registrar.norid.no/) in the same way you create other users there. For the test system RDAP, rdap.test.norid.no, [the test registrarweb](https://registrar.test.norid.no/), must be used.
*   The access right 'rdap\_access' must be set for the user.

### Access the service as an authenticated user

After the user has been created, it will be available for use after a few minutes.

The service can now be accessed with a client supporting _basic authentication_. The full username to be used in the query is on the form _<username@regid>_.

The configuration and use of authentication in the RDAP client will depend on the software which is used. In the following examples, curl and wget are being used as clients. Here, the registrar _reg9876_ authenticates with user _rdapuser_ and the password _mysecret123_.

Authenticated query using curl:

% curl --user rdapuser@reg9876:mysecret123 https://rdap.norid.no/domain/aa.no

Authenticated query using wget:

% wget -O - --auth-no-challenge --http-user=rdapuser@reg9876 --http-password=mysecret123 https://rdap.norid.no/domain/aa.no

#### Access restrictions for authenticated queries

For authenticated queries, the access is restricted by an IP filter. Each registrar must register the client IP that they want to use for the queries. This is done on the [registrar web](https://registrar.norid.no/), under _Settings_.

Extended data access
--------------------

Anonymous queries return results with restricted data content. With authenticated queries, more data becomes available.

### Domain lookup

For domain lookup, the result will contain information about the domain subscriber. The data returned for the domain subscriber is the same as in the direct query for the domain subscriber contact object (see next section).

### Contact object lookup (entity lookup)

Anonymous lookup for contact objects is only available for role contacts. Authenticated clients can lookup all contact types, i.e. roles, persons and organizations:

https://rdap.norid.no/entity/NT1O  
https://rdap.norid.no/entity/AA253P

The data content returned will depend on the contact type (role, person, organization), and on whether the registrar doing the lookup is the sponsoring registrar for the contact.

Searches
--------

Searches in RDAP makes it possible to retrieve lists of domains, contacts and nameservers, based on various search keys.

With anonymous access, only search on nameservers is available, with hostname as the key. With authenticated access, other search functions are available, as shown in the examples below.

The search result will only contain objects for which the client registrar is the sponsoring registrar of the object. For some search keys, the wildcard character _\*_ can be used. By default, the results from a search has a limited data content for each object. The complete object data can afterwards be retrieved with a direct lookup of the object.

See also section _Partial response_, on how to adjust the amount of data in the search result.

#### Examples on domain name searches:

https://rdap.norid.no/domains?name=nord\*.no

https://rdap.norid.no/domains?registrant=NT1O

https://rdap.norid.no/domains?identity=985821585

https://rdap.norid.no/domains?nsIp=128.39.8.40

https://rdap.norid.no/domains?nsLdhName=\*.labnic.no

#### Examples on nameserver searches:

https://rdap.norid.no/nameservers?name=\*.labnic.no

https://rdap.norid.no/nameservers?ip=128.39.8.40

#### Examples on contact object searches:

https://rdap.norid.no/entities?fn=norid\*

https://rdap.norid.no/entities?identity=985821585

### Paging and counting

For searches with many hits, the result message will only contain the first results. The result will additionally have a reference to a search query for the next results, making it possible to browse through the complete set of results. By using the parameter 'count=true', the result message will show a count of the total number of results:

Example: https://rdap.norid.no/domains?name=nord\*.no&count=true

The returned message contains a link which can be followed to the next page:

```
    "paging_metadata": {
        "links": [
            {
                "href": "https://rdap.norid.no/domains?name=nord*.no&cursor=O1GW1xKrewPkUHzQwIrTTQ%3D%3D&count=1",
                "rel": "next",
                ...
```


### Sorting

It is possible to set the sorting order of the results in the result message.

*   For domains, the following sorting keys can be used: registrationDate, lastChangedDate, expirationDate, name
*   For nameservers, the following sorting keys can be used: registrationDate, lastChangedDate, name
*   For contact objects, the following sorting keys can be used: registrationDate, lastChangedDate, handle, fn, org, country, cc, city

Sorting on expiration date:

https://rdap.norid.no/domains?name=nord\*.no&sort=expirationDate

Sorting on expiration date, descending:

https://rdap.norid.no/domains?name=nord\*.no&sort=expirationDate:d

Sorting on country code, then city:

https://rdap.norid.no/entities?fn=norid\*&sort=cc,city

### Partial response in searches

By default, the result message from a search contains limited data for each of the objects. With the parameter 'fieldSet' it is possible to change this. Setting it to the value 'fieldSet=full', complete data for each object is returned. Setting it the value 'fieldSet=id', the default limited data amount is returned.

Examples:

https://rdap.norid.no/domains?name=nord\*.no&fieldSet=full  
https://rdap.norid.no/domains?name=nord\*.no&fieldSet=id

Rate limiting
-------------

The RDAP service has two rate limits — both limit the number of lookups made from any given IP address.

One rate limit allows a maximum of 300 GET queries from any one IP address and 3000 HEAD queries per 24 hours in a sliding window. The other rate limit allows each IP address access to a maximum of 10 lookups (GET or HEAD) per minute.

If either of these limits is exceeded, lookups will return _429 Too many requests_.

Software for RDAP clients
-------------------------

RDAP is a web service, so any web browser can, in principle, be used as an RDAP client, as long as it is capable of receiving and presenting JSON data.

Command-line clients, such as wget and curl, can be used to retrieve data for scripting:

There are other, more specialized clients that can present JSON data in a more readable way. The following clients are available in open source code:

[OpenRDAP](https://www.openrdap.org/) - command line client written in Go.

[NicInfo](https://github.com/arineng/nicinfo) - command line client written in Ruby.

References
----------

A detailed description of how the service works can be found in the RFC specifications for the RDAP protocol:

*   [RFC7480](https://tools.ietf.org/html/rfc7480)
*   [RFC7481](https://tools.ietf.org/html/rfc7481)
*   [RFC9082](https://tools.ietf.org/html/rfc9082)
*   [RFC9083](https://tools.ietf.org/html/rfc9083)

RDAP extensions and related RFC documents

*   [RFC2617](https://www.rfc-editor.org/rfc/rfc2617) (http basic authentication)
*   [RFC8977](https://www.rfc-editor.org/rfc/rfc8977) (paging og sorting)
*   [RFC8982](https://www.rfc-editor.org/rfc/rfc8982) (partial response)

Published: 8 July 2020  
Updated: 30 September 2025