# The whois service – Norid
*   [Integrate with Norid](https://teknisk.norid.no/en/integrere-mot-norid/) /  
*   The whois service 

The whois service is a service where the general public can look up and find registered information about a domain name. The whois service has largely been phased out in favour of the public service, and also returns less data.

Access
------

The service is available at:

```
Host: whois.norid.no
Port: 43
```


As protection against potential abuse, the whois service has a built-in mechanism for rate limiting. This limits the number of queries, so you cannot submit a large number of queries at the same time.

Testing
-------

The service is available at:

```
Host: whois.test.norid.no
Port: 43
```


Example of use (requires that you have a whois client installed):

```
whois -h whois.test.norid.no draupne.no
```


Presents the data registered for the domain name _draupne.no_.

If you are looking up an IDN domain, you must specify the appropriate UTF-8 character set:

```
whois -h whois.test.norid.no -- -c utf-8 ole-žóòôöšŧüžon-æøå.no
```


Presents the data registered for the domain name _ole-žóòôöšŧüžon-æøå.no_.

Technical documentation
-----------------------



* Interface document for whois and DAS: Updated:2018-08-10: Rev. 10e1 with adjusted pretext, see Document History for description2018-05-23: Rev. 9e1 for new data model and GDPR, see Document History for description
* Interface document for whois and DAS: Description:This document describes the interface for both whois and DAS (Domain Availability Service).
* Interface document for whois and DAS: Document:Download Whois DAS Interface Specification v10e1 (PDF, 220KB)


Published: 8 July 2020  
Updated: 20 August 2020