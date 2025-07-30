adjusted_perc <- function(h, d, a) {
  h <- h * 100
  d <- d * 100
  a <- a * 100
  
  h_int <- round(h)
  d_int <- round(d)
  a_int <- round(a)
  
  sum_values <- h_int + a_int + d_int
  
  if (sum_values == 99) {
    max_decimal <- max(h %% 1, a %% 1, d %% 1)
    if (h %% 1 == max_decimal) {
      h_int <- h_int + 1
    } else if (a %% 1 == max_decimal) {
      a_int <- a_int + 1
    } else if (d %% 1 == max_decimal) {
      d_int <- d_int + 1
    }
  }
  
  if (sum_values == 101) {
    min_decimal <- min(h %% 1, d %% 1, a %% 1)
    if (h %% 1 == min_decimal) {
      h_int <- h_int - 1
    } else if (d %% 1 == min_decimal) {
      d_int <- d_int - 1
    } else if (a %% 1 == min_decimal) {
      a_int <- a_int - 1
    }
  }
  
  return(list(H = h_int, D = d_int, A = a_int))
}