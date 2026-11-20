-- Accuracy: revenue by customer group equals revenue by purchase channel (two independent views).
select * from (
  select (select sum(net_revenue) from {{ ref('rpt_segments') }}) as by_group,
         (select sum(net_revenue) from {{ ref('rpt_channel_purchase') }}) as by_channel
) where abs(by_group - by_channel) > 10
